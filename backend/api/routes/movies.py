"""
Movie endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from models.api_models import MovieDetail, MovieSummary, SearchResponse, GenreResponse, StatsResponse
from config.settings import get_settings
import certifi

settings = get_settings()
router = APIRouter(prefix="/movies", tags=["movies"])


def get_db():
    """Get database connection"""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    return client[settings.mongodb_db_name]


@router.get("/", response_model=SearchResponse)
async def get_movies(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    genre: Optional[str] = None,
    min_rating: float = Query(default=0.0, ge=0.0, le=10.0),
    sort_by: str = Query(default="popularity", regex="^(popularity|vote_average|release_date)$")
):
    """
    Get list of movies with optional filters

    Args:
        skip: Number of movies to skip (pagination)
        limit: Maximum number of movies to return
        genre: Filter by genre name
        min_rating: Minimum vote average
        sort_by: Sort field (popularity, vote_average, release_date)
    """
    db = get_db()

    # Build query
    query = {}
    if genre:
        query["genres.name"] = {"$regex": f"^{genre}$", "$options": "i"}
    if min_rating > 0:
        query["vote_average"] = {"$gte": min_rating}

    # Get total count
    total = await db.movies.count_documents(query)

    # Get movies
    sort_order = -1  # Descending
    movies = await db.movies.find(query).sort(
        sort_by, sort_order
    ).skip(skip).limit(limit).to_list(length=limit)

    # Format response
    movie_summaries = []
    for movie in movies:
        emotions = movie.get("emotions", {})
        movie_summaries.append(MovieSummary(
            id=movie["id"],
            title=movie["title"],
            release_date=movie.get("release_date"),
            vote_average=movie.get("vote_average", 0),
            popularity=movie.get("popularity", 0),
            poster_path=movie.get("poster_path"),
            genres=[g["name"] for g in movie.get("genres", [])],
            dominant_emotion=emotions.get("dominant_emotion")
        ))

    return SearchResponse(
        movies=movie_summaries,
        total=total,
        query=f"skip={skip}&limit={limit}"
    )


@router.get("/{movie_id}", response_model=MovieDetail)
async def get_movie_details(movie_id: int):
    """
    Get detailed information about a specific movie

    Args:
        movie_id: TMDB movie ID
    """
    db = get_db()

    movie = await db.movies.find_one({"id": movie_id})

    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")

    # Remove MongoDB _id
    movie.pop("_id", None)

    return MovieDetail(**movie)


@router.get("/{movie_id}/emotions")
async def get_movie_emotions(movie_id: int):
    """
    Get emotion profile for a specific movie.
    If no BERT-analyzed emotions exist, generates emotions from genres.

    Args:
        movie_id: TMDB movie ID
    """
    db = get_db()

    movie = await db.movies.find_one(
        {"id": movie_id},
        {"emotions": 1, "title": 1, "genres": 1, "_id": 0}
    )

    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")

    # Ensure all 6 base emotions are always present
    base_emotion_keys = ["joy", "sadness", "fear", "anger", "surprise", "disgust"]
    
    if "emotions" in movie and movie["emotions"]:
        emotions = movie["emotions"].copy()
        # Add missing base emotions with default value 0
        for emotion in base_emotion_keys:
            if emotion not in emotions:
                emotions[emotion] = 0.0
        return {
            "movie_id": movie_id,
            "title": movie["title"],
            "emotions": emotions
        }
    
    # Generate emotions from genres if no BERT analysis exists
    emotions = _generate_emotions_from_genres(movie.get("genres", []))
    
    return {
        "movie_id": movie_id,
        "title": movie["title"],
        "emotions": emotions,
        "source": "genre-based"
    }


def _generate_emotions_from_genres(genres: list) -> dict:
    """Generate emotion profile from movie genres"""
    genre_emotions = {
        "Action": {"thrill": 0.8, "fear": 0.4, "surprise": 0.6, "anger": 0.3, "joy": 0.5},
        "Adventure": {"joy": 0.7, "thrill": 0.7, "surprise": 0.6, "inspiration": 0.5},
        "Animation": {"joy": 0.8, "humor": 0.6, "surprise": 0.4},
        "Comedy": {"joy": 0.9, "humor": 0.9, "surprise": 0.3},
        "Crime": {"fear": 0.5, "anger": 0.6, "thrill": 0.6, "sadness": 0.3},
        "Documentary": {"inspiration": 0.5, "surprise": 0.3, "sadness": 0.2},
        "Drama": {"sadness": 0.6, "joy": 0.3, "anger": 0.3, "inspiration": 0.4},
        "Family": {"joy": 0.8, "humor": 0.5, "romance": 0.3},
        "Fantasy": {"joy": 0.6, "surprise": 0.7, "thrill": 0.5, "inspiration": 0.5},
        "History": {"sadness": 0.4, "inspiration": 0.5, "anger": 0.3},
        "Horror": {"fear": 0.9, "disgust": 0.5, "surprise": 0.6, "thrill": 0.8},
        "Music": {"joy": 0.8, "romance": 0.4, "inspiration": 0.6},
        "Mystery": {"fear": 0.5, "surprise": 0.7, "thrill": 0.6},
        "Romance": {"romance": 0.9, "joy": 0.7, "sadness": 0.3},
        "Science Fiction": {"thrill": 0.6, "surprise": 0.7, "fear": 0.4, "inspiration": 0.5},
        "TV Movie": {"joy": 0.4, "sadness": 0.3},
        "Thriller": {"fear": 0.7, "thrill": 0.9, "surprise": 0.6, "anger": 0.4},
        "War": {"anger": 0.6, "sadness": 0.7, "fear": 0.5},
        "Western": {"thrill": 0.6, "anger": 0.4, "joy": 0.3}
    }
    
    genre_names = [g.get("name", "") if isinstance(g, dict) else g for g in genres]
    
    combined_emotions = {
        "joy": 0.0, "sadness": 0.0, "fear": 0.0, "anger": 0.0,
        "surprise": 0.0, "disgust": 0.0, "thrill": 0.0, 
        "romance": 0.0, "humor": 0.0, "inspiration": 0.0
    }
    
    for genre_name in genre_names:
        if genre_name in genre_emotions:
            for emotion, score in genre_emotions[genre_name].items():
                combined_emotions[emotion] = max(combined_emotions[emotion], score)
    
    # Find dominant emotion
    base_emotions = {k: combined_emotions.get(k, 0) for k in ["joy", "sadness", "fear", "anger", "surprise", "disgust"]}
    dominant = max(base_emotions, key=base_emotions.get) if any(base_emotions.values()) else "joy"
    
    return {
        **combined_emotions,
        "dominant_emotion": dominant
    }


@router.get("/search/query", response_model=SearchResponse)
async def search_movies(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Search movies by title

    Args:
        q: Search query
        limit: Maximum number of results
    """
    db = get_db()

    # Search by title (case-insensitive)
    query = {"title": {"$regex": q, "$options": "i"}}

    movies = await db.movies.find(query).limit(limit).to_list(length=limit)

    # Format response
    movie_summaries = []
    for movie in movies:
        emotions = movie.get("emotions", {})
        movie_summaries.append(MovieSummary(
            id=movie["id"],
            title=movie["title"],
            release_date=movie.get("release_date"),
            vote_average=movie.get("vote_average", 0),
            popularity=movie.get("popularity", 0),
            poster_path=movie.get("poster_path"),
            genres=[g["name"] for g in movie.get("genres", [])],
            dominant_emotion=emotions.get("dominant_emotion")
        ))

    return SearchResponse(
        movies=movie_summaries,
        total=len(movie_summaries),
        query=q
    )


@router.get("/genres/list", response_model=GenreResponse)
async def get_genres():
    """
    Get list of all genres in the database
    """
    db = get_db()

    # Aggregate to get unique genres
    pipeline = [
        {"$unwind": "$genres"},
        {"$group": {
            "_id": "$genres.id",
            "name": {"$first": "$genres.name"}
        }},
        {"$sort": {"name": 1}}
    ]

    genres = await db.movies.aggregate(pipeline).to_list(length=None)

    # Format response
    genre_list = [{"id": g["_id"], "name": g["name"]} for g in genres]

    return GenreResponse(genres=genre_list)


@router.get("/stats/overview", response_model=StatsResponse)
async def get_stats():
    """
    Get database statistics
    """
    db = get_db()

    # Total movies
    total_movies = await db.movies.count_documents({})

    # Movies with emotions
    movies_with_emotions = await db.movies.count_documents({
        "emotions": {"$exists": True}
    })

    # Emotion distribution
    pipeline = [
        {"$match": {"emotions": {"$exists": True}}},
        {"$group": {
            "_id": "$emotions.dominant_emotion",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]

    emotion_dist = await db.movies.aggregate(pipeline).to_list(length=None)
    emotion_distribution = {e["_id"]: e["count"] for e in emotion_dist}

    # Top genres
    genre_pipeline = [
        {"$unwind": "$genres"},
        {"$group": {
            "_id": "$genres.name",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    top_genres_data = await db.movies.aggregate(genre_pipeline).to_list(length=10)
    top_genres = [{"name": g["_id"], "count": g["count"]} for g in top_genres_data]

    return StatsResponse(
        total_movies=total_movies,
        movies_with_emotions=movies_with_emotions,
        emotion_distribution=emotion_distribution,
        top_genres=top_genres
    )
