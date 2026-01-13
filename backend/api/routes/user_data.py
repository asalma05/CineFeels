"""
User data routes - Watchlist, Analysis History, Stats
Persistent data storage with Neo4j
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from api.routes.auth import get_current_user
from services.user_service import get_user_service

router = APIRouter(prefix="/user", tags=["user-data"])


# ===== Pydantic Models =====

class WatchlistItem(BaseModel):
    movie_id: int
    title: str
    poster_path: Optional[str] = ""
    vote_average: Optional[float] = 0


class WatchlistResponse(BaseModel):
    id: int
    title: str
    poster_path: Optional[str]
    vote_average: Optional[float]
    added_at: Optional[str]


class AnalysisCreate(BaseModel):
    emotions: dict
    movie_count: int


class AnalysisResponse(BaseModel):
    id: str
    emotions: dict
    movieCount: int
    date: str


class UserStats(BaseModel):
    total_analyses: int
    total_movies: int
    watchlist_count: int
    total_favorites: int = 0
    emotion_profile: dict


class EmotionProfile(BaseModel):
    joy: float = 0.0
    sadness: float = 0.0
    fear: float = 0.0
    anger: float = 0.0
    surprise: float = 0.0
    disgust: float = 0.0


# ===== Watchlist Endpoints =====

@router.get("/watchlist", response_model=List[WatchlistResponse])
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    """Get current user's watchlist"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    watchlist = await user_service.get_watchlist(email)
    return watchlist


@router.post("/watchlist", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    item: WatchlistItem,
    current_user: dict = Depends(get_current_user)
):
    """Add a movie to watchlist"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    success = await user_service.add_to_watchlist(
        email=email,
        movie_id=item.movie_id,
        title=item.title,
        poster_path=item.poster_path or "",
        vote_average=item.vote_average or 0
    )
    
    if success:
        return {"message": "Movie added to watchlist", "movie_id": item.movie_id}
    raise HTTPException(status_code=400, detail="Failed to add movie to watchlist")


@router.delete("/watchlist/{movie_id}")
async def remove_from_watchlist(
    movie_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a movie from watchlist"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    success = await user_service.remove_from_watchlist(email, movie_id)
    
    if success:
        return {"message": "Movie removed from watchlist", "movie_id": movie_id}
    raise HTTPException(status_code=404, detail="Movie not found in watchlist")


@router.delete("/watchlist")
async def clear_watchlist(current_user: dict = Depends(get_current_user)):
    """Clear entire watchlist"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    deleted_count = await user_service.clear_watchlist(email)
    return {"message": f"Cleared {deleted_count} movies from watchlist"}


@router.get("/watchlist/{movie_id}/check")
async def check_in_watchlist(
    movie_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Check if a movie is in watchlist"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    is_in = await user_service.is_in_watchlist(email, movie_id)
    return {"movie_id": movie_id, "in_watchlist": is_in}


# ===== Analysis History Endpoints =====

@router.get("/analyses", response_model=List[AnalysisResponse])
async def get_analysis_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get user's analysis history"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    history = await user_service.get_analysis_history(email, limit)
    
    # Format the response
    formatted = []
    for item in history:
        formatted.append({
            "id": str(item.get("id", "")),
            "emotions": item.get("emotions", {}),
            "movieCount": item.get("movieCount", 0),
            "date": str(item.get("date", ""))
        })
    
    return formatted


@router.post("/analyses", status_code=status.HTTP_201_CREATED)
async def save_analysis(
    analysis: AnalysisCreate,
    current_user: dict = Depends(get_current_user)
):
    """Save an emotion analysis"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    result = await user_service.save_analysis(
        email=email,
        emotions=analysis.emotions,
        movie_count=analysis.movie_count
    )
    
    if result:
        return {
            "message": "Analysis saved",
            "id": str(result.get("id", "")),
            "date": str(result.get("date", ""))
        }
    raise HTTPException(status_code=400, detail="Failed to save analysis")


# ===== Emotion Profile Endpoints =====

@router.get("/profile/emotions", response_model=EmotionProfile)
async def get_emotion_profile(current_user: dict = Depends(get_current_user)):
    """Get user's aggregate emotion profile"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    profile = await user_service.get_emotion_profile(email)
    return profile


# ===== User Stats Endpoints =====

@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get comprehensive user statistics"""
    user_service = get_user_service()
    email = current_user.get("email")
    
    stats = await user_service.get_user_stats_by_email(email)
    
    return {
        "total_analyses": stats.get("total_analyses", 0),
        "total_movies": stats.get("total_movies", 0),
        "watchlist_count": stats.get("watchlist_count", 0),
        "total_favorites": 0,  # Can be expanded later
        "emotion_profile": stats.get("emotion_profile", {})
    }
