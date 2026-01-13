"""
Mock recommendation endpoints - Temporary solution for MongoDB SSL issues
"""
from fastapi import APIRouter
from models.api_models import MoodRequest, RecommendationResponse, MovieSummary

router = APIRouter(prefix="/recommendations", tags=["recommendations-mock"])

# Mock movie data organized by mood
MOOD_MOVIES = {
    "happy": [
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
            "id": 19404,
            "title": "Dilwale Dulhania Le Jayenge",
            "release_date": "1995-10-20",
            "vote_average": 8.7,
            "popularity": 35.4,
            "poster_path": "/2CAL2433ZeIihfX1Hb2139CX0pW.jpg",
            "genres": ["Comedy", "Drama", "Romance"],
            "dominant_emotion": "romance"
        }
    ],
    "scary": [
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
        }
    ],
    "romantic": [
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
        }
    ],
    "sad": [
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
            "id": 424,
            "title": "Schindler's List",
            "release_date": "1993-12-15",
            "vote_average": 8.6,
            "popularity": 53.2,
            "poster_path": "/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
            "genres": ["Drama", "History", "War"],
            "dominant_emotion": "sadness"
        }
    ],
    "excited": [
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
            "id": 550,
            "title": "Fight Club",
            "release_date": "1999-10-15",
            "vote_average": 8.4,
            "popularity": 54.5,
            "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
            "genres": ["Drama", "Thriller"],
            "dominant_emotion": "thrill"
        }
    ],
    "thoughtful": [
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
        }
    ],
    "adventurous": [
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
            "id": 155,
            "title": "The Dark Knight",
            "release_date": "2008-07-16",
            "vote_average": 8.5,
            "popularity": 70.2,
            "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
            "genres": ["Action", "Crime", "Drama"],
            "dominant_emotion": "thrill"
        }
    ],
    "relaxed": [
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
            "id": 19404,
            "title": "Dilwale Dulhania Le Jayenge",
            "release_date": "1995-10-20",
            "vote_average": 8.7,
            "popularity": 35.4,
            "poster_path": "/2CAL2433ZeIihfX1Hb2139CX0pW.jpg",
            "genres": ["Comedy", "Drama", "Romance"],
            "dominant_emotion": "romance"
        }
    ],
    "nostalgic": [
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
            "id": 769,
            "title": "GoodFellas",
            "release_date": "1990-09-12",
            "vote_average": 8.5,
            "popularity": 45.7,
            "poster_path": "/aKuFiU82s5ISJpGZp7YkIr3kCUd.jpg",
            "genres": ["Crime", "Drama"],
            "dominant_emotion": "thrill"
        }
    ]
}


@router.post("/by-mood", response_model=RecommendationResponse)
async def get_recommendations_by_mood(request: MoodRequest):
    """Get movie recommendations based on mood"""
    mood = request.mood.lower()

    # Get movies for this mood, or default to happy
    movies_data = MOOD_MOVIES.get(mood, MOOD_MOVIES["happy"])

    # Convert to MovieSummary objects
    movies = [MovieSummary(**m) for m in movies_data]

    return RecommendationResponse(
        movies=movies,
        total=len(movies),
        query={"mood": request.mood, "limit": len(movies)}
    )
