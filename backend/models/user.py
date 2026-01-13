"""
User models for authentication and profile management
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class User(UserBase):
    """User model (without password)"""
    user_id: str
    created_at: datetime
    favorite_genres: List[str] = []
    favorite_emotions: dict = {}

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "moviefan",
                "full_name": "John Doe",
                "user_id": "user_123",
                "created_at": "2025-01-11T12:00:00",
                "favorite_genres": ["Action", "Thriller"],
                "favorite_emotions": {"joy": 0.7, "thrill": 0.8}
            }
        }


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None


class MovieInteraction(BaseModel):
    """User interaction with a movie"""
    movie_id: int
    rating: Optional[float] = Field(None, ge=0, le=10)
    liked: bool
    watched_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(User):
    """Extended user profile with stats"""
    total_movies_watched: int = 0
    total_movies_liked: int = 0
    top_genres: List[dict] = []
    recommendation_accuracy: Optional[float] = None
