"""
User service for authentication and profile management - Simple version (no Neo4j)
Uses in-memory storage with JSON file persistence
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from passlib.context import CryptContext
from jose import JWTError, jwt
import json
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "cinefeels-secret-key-2025-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Simple file-based storage
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')

# In-memory user store
_users_db: Dict[str, dict] = {}
_analysis_history: Dict[str, List[dict]] = {}


def _load_users():
    """Load users from file"""
    global _users_db
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                _users_db = json.load(f)
    except Exception as e:
        print(f"Could not load users: {e}")
        _users_db = {}


def _save_users():
    """Save users to file"""
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(_users_db, f, default=str)
    except Exception as e:
        print(f"Could not save users: {e}")


# Load users on module import
_load_users()


class UserService:
    """Service for user management - Simple version"""

    def __init__(self):
        pass

    # Password utilities
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    # JWT utilities
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    # User CRUD operations
    async def create_user(self, email: str, username: str, password: str, full_name: Optional[str] = None) -> dict:
        """Create a new user"""
        hashed_password = self.get_password_hash(password)
        user_id = f"user_{int(datetime.utcnow().timestamp() * 1000)}"
        
        user = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "created_at": datetime.utcnow().isoformat()
        }
        
        _users_db[email] = user
        _save_users()
        
        return user

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        return _users_db.get(email)

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username"""
        for user in _users_db.values():
            if user.get("username") == username:
                return user
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        return user

    async def get_user_stats(self, user_id: str) -> dict:
        """Get user statistics"""
        history = _analysis_history.get(user_id, [])
        return {
            "total_watched": len(history),
            "total_liked": 0,
            "avg_rating": 0.0
        }

    async def add_movie_interaction(self, user_id: str, movie_id: int, liked: bool, rating: float = None) -> bool:
        """Add movie interaction"""
        return True

    async def get_user_watched_movies(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get user's watched movies"""
        return []

    async def get_recommended_movies_for_user(self, user_id: str, limit: int = 10) -> List[int]:
        """Get recommended movie IDs for user"""
        return []

    async def get_recommendation_history(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get user's recommendation history"""
        return _analysis_history.get(user_id, [])[:limit]

    async def save_recommendation_history(self, user_id: str, movie_ids: list, mood: str, emotions: dict = None) -> bool:
        """Save recommendation to history"""
        if user_id not in _analysis_history:
            _analysis_history[user_id] = []
        
        _analysis_history[user_id].insert(0, {
            "date": datetime.utcnow().isoformat(),
            "mood": mood,
            "emotions": emotions or {},
            "movie_ids": movie_ids,
            "movie_count": len(movie_ids)
        })
        
        # Keep only last 50
        _analysis_history[user_id] = _analysis_history[user_id][:50]
        
        return True

    async def get_user_emotional_profile(self, user_id: str) -> Optional[dict]:
        """Get user's emotional profile"""
        history = _analysis_history.get(user_id, [])
        if not history:
            return None
        
        # Aggregate emotions from history
        totals = {}
        counts = {}
        
        for entry in history:
            for emotion, value in entry.get("emotions", {}).items():
                totals[emotion] = totals.get(emotion, 0) + value
                counts[emotion] = counts.get(emotion, 0) + 1
        
        profile = {}
        for emotion in totals:
            profile[emotion] = totals[emotion] / counts[emotion]
        
        return profile

    async def update_user_emotional_profile(self, user_id: str, emotions: dict) -> bool:
        """Update user's emotional profile"""
        return True

    async def add_movie_review(self, user_id: str, movie_id: int, review_text: str, emotions_detected: dict) -> bool:
        """Add a movie review"""
        return True

    async def get_user_reviews(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get user's movie reviews"""
        return []


# Singleton instance
_user_service_instance = None


def get_user_service() -> UserService:
    """Get UserService singleton instance"""
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance
