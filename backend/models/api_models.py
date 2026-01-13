"""
API Request/Response models for CineFeels
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from models.emotion import EmotionProfile


class RecommendationRequest(BaseModel):
    """Request for movie recommendations"""
    emotions: Dict[str, float] = Field(
        description="Emotion scores (0-1) for desired mood",
        example={"joy": 0.8, "thrill": 0.6}
    )
    limit: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    min_rating: float = Field(default=0.0, ge=0.0, le=10.0, description="Minimum movie rating")


class MoodRequest(BaseModel):
    """Request for mood-based recommendations"""
    mood: str = Field(
        description="Mood keyword",
        example="happy"
    )
    limit: int = Field(default=10, ge=1, le=50)
    min_rating: float = Field(default=6.0, ge=0.0, le=10.0)


class MovieSummary(BaseModel):
    """Summary of a movie for list responses"""
    id: int
    title: str
    release_date: Optional[str]
    vote_average: float
    popularity: float
    poster_path: Optional[str]
    genres: List[str]
    dominant_emotion: Optional[str] = None
    similarity_score: Optional[float] = None


class MovieDetail(BaseModel):
    """Detailed movie information"""
    id: int
    title: str
    overview: Optional[str]
    release_date: Optional[str]
    vote_average: float
    vote_count: int
    popularity: float
    runtime: Optional[int]
    budget: Optional[int]
    revenue: Optional[int]
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    genres: List[Dict[str, Any]]
    emotions: Optional[Dict] = None


class RecommendationResponse(BaseModel):
    """Response with movie recommendations"""
    movies: List[MovieSummary]
    total: int
    query: Dict


class SearchResponse(BaseModel):
    """Response for search results"""
    movies: List[MovieSummary]
    total: int
    query: str


class GenreResponse(BaseModel):
    """Response with list of genres"""
    genres: List[Dict[str, Any]]


class StatsResponse(BaseModel):
    """Database statistics response"""
    total_movies: int
    movies_with_emotions: int
    emotion_distribution: Dict[str, int]
    top_genres: List[Dict[str, Any]]
