"""
Recommendation endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from models.api_models import (
    RecommendationRequest,
    MoodRequest,
    RecommendationResponse,
    MovieSummary
)
from services.recommendation_service import get_recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get movie recommendations based on emotion preferences

    Example request:
    ```json
    {
      "emotions": {
        "joy": 0.8,
        "thrill": 0.6
      },
      "limit": 10,
      "min_rating": 6.0
    }
    ```
    """
    service = get_recommendation_service()

    recommendations = await service.recommend_by_emotions(
        user_emotions=request.emotions,
        limit=request.limit,
        min_rating=request.min_rating
    )

    # Format response
    movies = []
    for rec in recommendations:
        movie = rec["movie"]
        emotions = movie.get("emotions", {})

        movies.append(MovieSummary(
            id=movie["id"],
            title=movie["title"],
            release_date=movie.get("release_date"),
            vote_average=movie.get("vote_average", 0),
            popularity=movie.get("popularity", 0),
            poster_path=movie.get("poster_path"),
            genres=[g["name"] for g in movie.get("genres", [])],
            dominant_emotion=emotions.get("dominant_emotion"),
            similarity_score=rec["similarity_score"]
        ))

    return RecommendationResponse(
        movies=movies,
        total=len(movies),
        query=request.dict()
    )


@router.post("/by-mood", response_model=RecommendationResponse)
async def get_recommendations_by_mood(request: MoodRequest):
    """
    Get movie recommendations based on a mood keyword

    Supported moods:
    - happy, joyful, cheerful
    - scary, terrifying, horror
    - thrilling, exciting, suspenseful
    - sad, emotional, tearjerker
    - romantic, love
    - funny, comedy, hilarious
    - inspiring, motivational, uplifting
    - angry, intense
    - surprising, mindblowing

    Example request:
    ```json
    {
      "mood": "happy",
      "limit": 10,
      "min_rating": 6.0
    }
    ```
    """
    service = get_recommendation_service()

    recommendations = await service.recommend_by_mood(
        mood=request.mood,
        limit=request.limit,
        min_rating=request.min_rating
    )

    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail=f"No movies found for mood '{request.mood}'"
        )

    # Format response
    movies = []
    for rec in recommendations:
        movie = rec["movie"]
        emotions = movie.get("emotions", {})

        movies.append(MovieSummary(
            id=movie["id"],
            title=movie["title"],
            release_date=movie.get("release_date"),
            vote_average=movie.get("vote_average", 0),
            popularity=movie.get("popularity", 0),
            poster_path=movie.get("poster_path"),
            genres=[g["name"] for g in movie.get("genres", [])],
            dominant_emotion=emotions.get("dominant_emotion"),
            similarity_score=rec["similarity_score"]
        ))

    return RecommendationResponse(
        movies=movies,
        total=len(movies),
        query=request.dict()
    )


@router.get("/similar/{movie_id}", response_model=RecommendationResponse)
async def get_similar_movies(
    movie_id: int,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Get movies similar to a given movie based on emotional profile

    Args:
        movie_id: TMDB movie ID
        limit: Maximum number of similar movies
    """
    service = get_recommendation_service()

    similar_movies = await service.get_similar_movies(
        movie_id=movie_id,
        limit=limit
    )

    if not similar_movies:
        raise HTTPException(
            status_code=404,
            detail=f"Movie with ID {movie_id} not found or has no emotion data"
        )

    # Format response
    movies = []
    for rec in similar_movies:
        movie = rec["movie"]
        emotions = movie.get("emotions", {})

        movies.append(MovieSummary(
            id=movie["id"],
            title=movie["title"],
            release_date=movie.get("release_date"),
            vote_average=movie.get("vote_average", 0),
            popularity=movie.get("popularity", 0),
            poster_path=movie.get("poster_path"),
            genres=[g["name"] for g in movie.get("genres", [])],
            dominant_emotion=emotions.get("dominant_emotion"),
            similarity_score=rec["similarity_score"]
        ))

    return RecommendationResponse(
        movies=movies,
        total=len(movies),
        query={"movie_id": movie_id, "limit": limit}
    )


@router.get("/by-emotion/{emotion}", response_model=RecommendationResponse)
async def get_by_dominant_emotion(
    emotion: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Get movies by dominant emotion

    Available emotions:
    - joy
    - fear
    - sadness
    - anger
    - surprise
    - disgust
    - neutral

    Args:
        emotion: Dominant emotion name
        limit: Maximum number of movies
    """
    service = get_recommendation_service()

    movies_data = await service.get_by_emotion_distribution(
        dominant_emotion=emotion.lower(),
        limit=limit
    )

    if not movies_data:
        raise HTTPException(
            status_code=404,
            detail=f"No movies found with dominant emotion '{emotion}'"
        )

    # Format response
    movies = []
    for rec in movies_data:
        movie = rec["movie"]
        emotions = movie.get("emotions", {})

        movies.append(MovieSummary(
            id=movie["id"],
            title=movie["title"],
            release_date=movie.get("release_date"),
            vote_average=movie.get("vote_average", 0),
            popularity=movie.get("popularity", 0),
            poster_path=movie.get("poster_path"),
            genres=[g["name"] for g in movie.get("genres", [])],
            dominant_emotion=emotions.get("dominant_emotion"),
            similarity_score=None
        ))

    return RecommendationResponse(
        movies=movies,
        total=len(movies),
        query={"emotion": emotion, "limit": limit}
    )
