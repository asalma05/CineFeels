"""
Mock movie endpoints - Temporary solution for MongoDB SSL issues
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from models.api_models import MovieDetail, MovieSummary, SearchResponse, GenreResponse, StatsResponse

router = APIRouter(prefix="/movies-mock", tags=["movies-mock"])

# Mock movie data
MOCK_MOVIES = [
    {
        "id": 550,
        "title": "Fight Club",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "popularity": 54.5,
        "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "genres": ["Drama", "Thriller"],
        "dominant_emotion": "thrill"
    },
    {
        "id": 13,
        "title": "Forrest Gump",
        "release_date": "1994-07-06",
        "vote_average": 8.5,
        "popularity": 62.3,
        "poster_path": "/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg",
        "genres": ["Comedy", "Drama", "Romance"],
        "dominant_emotion": "joy"
    },
    {
        "id": 680,
        "title": "Pulp Fiction",
        "release_date": "1994-09-10",
        "vote_average": 8.5,
        "popularity": 58.1,
        "poster_path": "/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
        "genres": ["Crime", "Drama"],
        "dominant_emotion": "thrill"
    },
    {
        "id": 155,
        "title": "The Dark Knight",
        "release_date": "2008-07-16",
        "vote_average": 8.5,
        "popularity": 70.2,
        "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "genres": ["Action", "Crime", "Drama"],
        "dominant_emotion": "thrill"
    },
    {
        "id": 497,
        "title": "The Green Mile",
        "release_date": "1999-12-10",
        "vote_average": 8.5,
        "popularity": 48.9,
        "poster_path": "/velWPhVMQeQKcxggNEU8YmIo52R.jpg",
        "genres": ["Crime", "Drama", "Fantasy"],
        "dominant_emotion": "sadness"
    },
    {
        "id": 769,
        "title": "GoodFellas",
        "release_date": "1990-09-12",
        "vote_average": 8.5,
        "popularity": 45.7,
        "poster_path": "/aKuFiU82s5ISJpGZp7YkIr3kCUd.jpg",
        "genres": ["Crime", "Drama"],
        "dominant_emotion": "thrill"
    },
    {
        "id": 122,
        "title": "The Lord of the Rings: The Return of the King",
        "release_date": "2003-12-01",
        "vote_average": 8.5,
        "popularity": 65.4,
        "poster_path": "/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg",
        "genres": ["Action", "Adventure", "Fantasy"],
        "dominant_emotion": "thrill"
    },
    {
        "id": 278,
        "title": "The Shawshank Redemption",
        "release_date": "1994-09-23",
        "vote_average": 8.7,
        "popularity": 82.1,
        "poster_path": "/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
        "genres": ["Crime", "Drama"],
        "dominant_emotion": "joy"
    },
    {
        "id": 238,
        "title": "The Godfather",
        "release_date": "1972-03-14",
        "vote_average": 8.7,
        "popularity": 71.3,
        "poster_path": "/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
        "genres": ["Crime", "Drama"],
        "dominant_emotion": "thrill"
    },
    {
        "id": 424,
        "title": "Schindler's List",
        "release_date": "1993-12-15",
        "vote_average": 8.6,
        "popularity": 53.2,
        "poster_path": "/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
        "genres": ["Drama", "History", "War"],
        "dominant_emotion": "sadness"
    },
    {
        "id": 19404,
        "title": "Dilwale Dulhania Le Jayenge",
        "release_date": "1995-10-20",
        "vote_average": 8.7,
        "popularity": 35.4,
        "poster_path": "/2CAL2433ZeIihfX1Hb2139CX0pW.jpg",
        "genres": ["Comedy", "Drama", "Romance"],
        "dominant_emotion": "romance"
    },
    {
        "id": 372058,
        "title": "Your Name",
        "release_date": "2016-08-26",
        "vote_average": 8.5,
        "popularity": 42.7,
        "poster_path": "/q719jXXEzOoYaps6babgKnONONX.jpg",
        "genres": ["Animation", "Drama", "Fantasy", "Romance"],
        "dominant_emotion": "romance"
    }
]


@router.get("/", response_model=SearchResponse)
async def get_movies(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    genre: Optional[str] = None,
    min_rating: float = Query(default=0.0, ge=0.0, le=10.0),
    sort_by: str = Query(default="popularity", regex="^(popularity|vote_average|release_date)$")
):
    """Get list of mock movies"""
    movies = [MovieSummary(**m) for m in MOCK_MOVIES]

    # Apply filters
    if genre:
        movies = [m for m in movies if genre.lower() in [g.lower() for g in m.genres]]
    if min_rating > 0:
        movies = [m for m in movies if m.vote_average >= min_rating]

    # Sort
    if sort_by == "vote_average":
        movies.sort(key=lambda x: x.vote_average, reverse=True)
    elif sort_by == "popularity":
        movies.sort(key=lambda x: x.popularity, reverse=True)

    # Pagination
    total = len(movies)
    movies = movies[skip:skip+limit]

    return SearchResponse(
        movies=movies,
        total=total,
        query=f"skip={skip}&limit={limit}"
    )


@router.get("/stats/overview", response_model=StatsResponse)
async def get_stats():
    """Get mock database statistics"""
    return StatsResponse(
        total_movies=len(MOCK_MOVIES),
        movies_with_emotions=len(MOCK_MOVIES),
        emotion_distribution={
            "thrill": 6,
            "joy": 2,
            "sadness": 2,
            "romance": 2
        },
        top_genres=[
            {"name": "Drama", "count": 10},
            {"name": "Crime", "count": 6},
            {"name": "Thriller", "count": 3},
            {"name": "Romance", "count": 3}
        ]
    )


@router.get("/genres/list", response_model=GenreResponse)
async def get_genres():
    """Get list of all genres"""
    genres_set = set()
    for movie in MOCK_MOVIES:
        genres_set.update(movie["genres"])

    genres = [{"id": i, "name": name} for i, name in enumerate(sorted(genres_set), start=1)]
    return GenreResponse(genres=genres)
