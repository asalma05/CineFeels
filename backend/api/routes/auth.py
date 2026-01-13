"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import timedelta
from typing import Optional

from models.user import (
    UserCreate,
    UserLogin,
    User,
    Token,
    TokenData,
    UserProfile,
    MovieInteraction
)
# Use Neo4j user service for persistent storage
from services.user_service import get_user_service, UserService, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user_service = get_user_service()
    user = await user_service.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    user_service = get_user_service()

    # Check if user already exists
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = await user_service.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    # Remove password from response
    user_response = {
        "email": user["email"],
        "username": user["username"],
        "full_name": user.get("full_name"),
        "user_id": user["user_id"],
        "created_at": user["created_at"],
        "favorite_genres": [],
        "favorite_emotions": {}
    }

    return user_response


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get JWT token"""
    user_service = get_user_service()

    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = user_service.create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile with stats"""
    user_service = get_user_service()
    stats = await user_service.get_user_stats(current_user["user_id"])

    return {
        "email": current_user["email"],
        "username": current_user["username"],
        "full_name": current_user.get("full_name"),
        "user_id": current_user["user_id"],
        "created_at": current_user["created_at"],
        "favorite_genres": [],
        "favorite_emotions": {},
        "total_movies_watched": stats["total_watched"],
        "total_movies_liked": stats["total_liked"],
        "top_genres": []
    }


@router.post("/movies/interact")
async def interact_with_movie(
    interaction: MovieInteraction,
    current_user: dict = Depends(get_current_user)
):
    """Record user interaction with a movie (like/watch/rate)"""
    user_service = get_user_service()

    success = await user_service.add_movie_interaction(
        user_id=current_user["user_id"],
        movie_id=interaction.movie_id,
        liked=interaction.liked,
        rating=interaction.rating
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record interaction"
        )

    return {"message": "Interaction recorded successfully"}


@router.get("/movies/history")
async def get_watch_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get user's watch history"""
    user_service = get_user_service()
    history = await user_service.get_user_watched_movies(
        current_user["user_id"],
        limit=limit
    )
    return {"history": history}


@router.get("/recommendations/personalized")
async def get_personalized_recommendations(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get personalized movie recommendations based on user's preferences"""
    user_service = get_user_service()

    # Get recommendations from Neo4j (collaborative filtering)
    movie_ids = await user_service.get_recommended_movies_for_user(
        current_user["user_id"],
        limit=limit
    )

    return {
        "user_id": current_user["user_id"],
        "recommended_movie_ids": movie_ids,
        "total": len(movie_ids)
    }


@router.get("/recommendations/history")
async def get_recommendation_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get user's recommendation history"""
    user_service = get_user_service()
    history = await user_service.get_recommendation_history(
        current_user["user_id"],
        limit=limit
    )
    return {"history": history, "total": len(history)}


@router.post("/recommendations/save")
async def save_recommendation_to_history(
    movie_ids: list,
    mood: str,
    emotions: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """Save a recommendation session to user's history"""
    user_service = get_user_service()
    success = await user_service.save_recommendation_history(
        user_id=current_user["user_id"],
        movie_ids=movie_ids,
        mood=mood,
        emotions=emotions or {}
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save recommendation history"
        )

    return {"message": "Recommendation saved to history"}


@router.post("/analysis/save")
async def save_analysis(
    emotions: dict,
    movie_ids: list,
    timestamp: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Save an emotion analysis session to user's history"""
    user_service = get_user_service()
    success = await user_service.save_recommendation_history(
        user_id=current_user["user_id"],
        movie_ids=movie_ids,
        mood="custom",
        emotions=emotions
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save analysis"
        )

    return {"message": "Analysis saved successfully"}



@router.get("/profile/emotional")
async def get_emotional_profile(current_user: dict = Depends(get_current_user)):
    """Get user's emotional profile for radar chart visualization"""
    user_service = get_user_service()
    profile = await user_service.get_user_emotional_profile(current_user["user_id"])

    # If no profile exists, return default
    if not profile:
        profile = {
            "thrill": 0.5,
            "joy": 0.5,
            "sadness": 0.5,
            "fear": 0.5,
            "surprise": 0.5,
            "humor": 0.5
        }

    return {
        "user_id": current_user["user_id"],
        "emotional_profile": profile
    }


@router.put("/profile/emotional")
async def update_emotional_profile(
    emotions: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user's emotional profile"""
    user_service = get_user_service()
    success = await user_service.update_user_emotional_profile(
        user_id=current_user["user_id"],
        emotions=emotions
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update emotional profile"
        )

    return {"message": "Emotional profile updated", "profile": emotions}


@router.post("/movies/review")
async def add_movie_review(
    movie_id: int,
    review_text: str,
    emotions_detected: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """Add a review for a movie with emotion analysis"""
    user_service = get_user_service()

    # TODO: Use BERT to analyze the review text and detect emotions
    # For now, accept emotions from frontend or use defaults
    if not emotions_detected:
        emotions_detected = {"joy": 0.5, "sadness": 0.3, "thrill": 0.2}

    success = await user_service.add_movie_review(
        user_id=current_user["user_id"],
        movie_id=movie_id,
        review_text=review_text,
        emotions_detected=emotions_detected
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add review"
        )

    return {"message": "Review added successfully", "emotions": emotions_detected}


@router.get("/movies/reviews")
async def get_user_reviews(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get user's movie reviews"""
    user_service = get_user_service()
    reviews = await user_service.get_user_reviews(
        current_user["user_id"],
        limit=limit
    )
    return {"reviews": reviews, "total": len(reviews)}


@router.get("/dashboard")
async def get_user_dashboard(current_user: dict = Depends(get_current_user)):
    """Get complete user dashboard data with all stats and visualizations"""
    user_service = get_user_service()

    # Get all user data in parallel
    stats = await user_service.get_user_stats(current_user["user_id"])
    emotional_profile = await user_service.get_user_emotional_profile(current_user["user_id"])
    watch_history = await user_service.get_user_watched_movies(current_user["user_id"], limit=10)
    recommendation_history = await user_service.get_recommendation_history(current_user["user_id"], limit=5)
    reviews = await user_service.get_user_reviews(current_user["user_id"], limit=5)

    # Default emotional profile if none exists
    if not emotional_profile:
        emotional_profile = {
            "thrill": 0.5, "joy": 0.5, "sadness": 0.5,
            "fear": 0.5, "surprise": 0.5, "humor": 0.5
        }

    return {
        "user": {
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "email": current_user["email"],
            "full_name": current_user.get("full_name"),
            "created_at": current_user.get("created_at")
        },
        "stats": {
            "total_watched": stats["total_watched"],
            "total_liked": stats["total_liked"],
            "avg_rating": stats["avg_rating"]
        },
        "emotional_profile": emotional_profile,
        "recent_watch_history": watch_history,
        "recent_recommendations": recommendation_history,
        "recent_reviews": reviews
    }
