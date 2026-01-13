from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # Application
    app_name: str = "CineFeels"
    app_env: str = "development"
    api_version: str = "v1"
    secret_key: str
    
    # MongoDB
    mongodb_uri: str
    mongodb_db_name: str = "cinefeels_db"
    
    # Neo4j
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    
    # External APIs
    tmdb_api_key: str
    hf_token: str = ""
    
    # AI Model
    emotion_model: str = "j-hartmann/emotion-english-distilroberta-base"
    
    # Emotion Dimensions
    emotion_dimensions: List[str] = [
        "joy", "sadness", "fear", "anger", 
        "surprise", "disgust", "neutral"
    ]
    
    # Custom CineFeels Emotions (mapped from base emotions)
    cinefeels_emotions: dict = {
        "thrill": ["fear", "surprise"],
        "joy": ["joy"],
        "sadness": ["sadness"],
        "fear": ["fear"],
        "humor": ["joy"],
        "surprise": ["surprise"],
        "romance": ["joy"],
        "inspiration": ["joy", "surprise"]
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()