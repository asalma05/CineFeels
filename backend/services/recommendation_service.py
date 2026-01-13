"""
Recommendation Service for CineFeels
"""
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import get_settings
import numpy as np
import logging

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for movie recommendations based on emotions"""

    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.mongodb_db_name]
        self.movies_collection = self.db.movies

    async def recommend_by_emotions(
        self,
        user_emotions: Dict[str, float],
        limit: int = 10,
        min_rating: float = 0.0
    ) -> List[Dict]:
        """
        Recommend movies based on user emotion preferences

        Args:
            user_emotions: Dict of emotion scores (e.g., {"joy": 0.8, "thrill": 0.6})
            limit: Maximum number of recommendations
            min_rating: Minimum movie rating filter

        Returns:
            List of recommended movies with similarity scores
        """
        logger.info(f"Getting recommendations for emotions: {user_emotions}")

        # Get all movies with emotion data
        query = {"emotions": {"$exists": True}}
        if min_rating > 0:
            query["vote_average"] = {"$gte": min_rating}

        movies = await self.movies_collection.find(query).to_list(length=None)

        if not movies:
            return []

        # Calculate similarity scores
        recommendations = []
        for movie in movies:
            similarity = self._calculate_similarity(user_emotions, movie)
            recommendations.append({
                "movie": movie,
                "similarity_score": similarity
            })

        # Sort by similarity score
        recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Return top N
        return recommendations[:limit]

    def _calculate_similarity(self, user_emotions: Dict[str, float], movie: Dict) -> float:
        """
        Calculate cosine similarity between user emotions and movie emotions

        Args:
            user_emotions: User's emotion preferences
            movie: Movie document with emotions

        Returns:
            Similarity score (0-1)
        """
        movie_emotions = movie.get("emotions", {})
        
        # If no emotions, generate from genres
        if not movie_emotions:
            movie_emotions = self._generate_emotions_from_genres(movie)

        # Build emotion vectors
        # Support both base emotions and CineFeels emotions
        emotion_keys = set(user_emotions.keys())

        user_vector = []
        movie_vector = []

        for emotion in emotion_keys:
            user_score = user_emotions.get(emotion, 0.0)

            # Check if it's a CineFeels emotion (thrill, romance, etc.)
            if emotion in ["thrill", "romance", "inspiration", "humor"]:
                movie_score = movie_emotions.get(emotion, 0.0)
            else:
                # It's a base emotion (joy, fear, etc.)
                # Try base_emotions first, then direct access for backward compatibility
                base_emotions = movie_emotions.get("base_emotions", {})
                if base_emotions:
                    movie_score = base_emotions.get(emotion, 0.0)
                else:
                    # Direct access (old format)
                    movie_score = movie_emotions.get(emotion, 0.0)

            user_vector.append(user_score)
            movie_vector.append(movie_score)

        # Calculate similarity score
        if not user_vector or not movie_vector:
            return 0.0

        user_array = np.array(user_vector)
        movie_array = np.array(movie_vector)

        # Use weighted similarity based on how well movie matches user preferences
        # Instead of cosine similarity (which gives 1.0 for single-emotion queries),
        # we calculate how much the movie's emotions match the user's requested emotions
        
        # Normalize user emotions to sum to 1 (importance weights)
        user_sum = np.sum(user_array)
        if user_sum == 0:
            return 0.0
        
        weights = user_array / user_sum
        
        # Calculate weighted average of movie emotions based on user preferences
        # Higher movie emotion = better match for that emotion
        weighted_match = np.sum(weights * movie_array)
        
        # Clamp to [0, 1]
        similarity = min(max(weighted_match, 0.0), 1.0)

        return float(similarity)

    async def get_similar_movies(
        self,
        movie_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find movies similar to a given movie

        Args:
            movie_id: TMDB movie ID
            limit: Maximum number of similar movies

        Returns:
            List of similar movies
        """
        # Get the reference movie
        reference_movie = await self.movies_collection.find_one({"id": movie_id})

        if not reference_movie or "emotions" not in reference_movie:
            return []

        # Extract emotion profile
        emotions = reference_movie.get("emotions", {})
        user_emotions = {
            "thrill": emotions.get("thrill", 0),
            "romance": emotions.get("romance", 0),
            "inspiration": emotions.get("inspiration", 0),
            "humor": emotions.get("humor", 0)
        }

        # Get recommendations (excluding the reference movie)
        all_recommendations = await self.recommend_by_emotions(user_emotions, limit=limit+1)

        # Filter out the reference movie
        similar_movies = [
            rec for rec in all_recommendations
            if rec["movie"].get("id") != movie_id
        ]

        return similar_movies[:limit]

    async def recommend_by_mood(
        self,
        mood: str,
        limit: int = 10,
        min_rating: float = 6.0
    ) -> List[Dict]:
        """
        Recommend movies based on a mood keyword

        Args:
            mood: Mood keyword (e.g., "happy", "scary", "sad", "thrilling")
            limit: Maximum number of recommendations
            min_rating: Minimum movie rating

        Returns:
            List of recommended movies
        """
        # Map moods to emotions
        mood_mappings = {
            "happy": {"joy": 1.0},
            "joyful": {"joy": 1.0},
            "cheerful": {"joy": 1.0},

            "scary": {"fear": 1.0, "thrill": 0.8},
            "terrifying": {"fear": 1.0},
            "horror": {"fear": 1.0},

            "thrilling": {"thrill": 1.0, "surprise": 0.6},
            "exciting": {"thrill": 0.8, "surprise": 0.7},
            "suspenseful": {"fear": 0.6, "surprise": 0.8},

            "sad": {"sadness": 1.0},
            "emotional": {"sadness": 0.7, "joy": 0.5},
            "tearjerker": {"sadness": 0.9},

            "romantic": {"romance": 1.0, "joy": 0.6},
            "love": {"romance": 1.0},

            "funny": {"humor": 1.0, "joy": 0.8},
            "comedy": {"humor": 1.0},
            "hilarious": {"humor": 1.0},

            "inspiring": {"inspiration": 1.0, "joy": 0.6},
            "motivational": {"inspiration": 1.0},
            "uplifting": {"inspiration": 0.8, "joy": 0.7},

            "angry": {"anger": 1.0},
            "intense": {"anger": 0.7, "thrill": 0.7},

            "surprising": {"surprise": 1.0},
            "mindblowing": {"surprise": 1.0, "inspiration": 0.5}
        }

        mood_lower = mood.lower().strip()
        emotions = mood_mappings.get(mood_lower, {"joy": 0.5})

        return await self.recommend_by_emotions(emotions, limit, min_rating)

    async def get_top_rated(self, limit: int = 10, genre: Optional[str] = None) -> List[Dict]:
        """
        Get top rated movies

        Args:
            limit: Maximum number of movies
            genre: Optional genre filter

        Returns:
            List of top rated movies
        """
        query = {}
        if genre:
            query["genres.name"] = {"$regex": f"^{genre}$", "$options": "i"}

        movies = await self.movies_collection.find(query).sort(
            "vote_average", -1
        ).limit(limit).to_list(length=limit)

        return [{"movie": movie, "similarity_score": 1.0} for movie in movies]

    async def get_by_emotion_distribution(
        self,
        dominant_emotion: str,
        limit: int = 10,
        min_score: float = 0.3
    ) -> List[Dict]:
        """
        Get movies by dominant emotion

        Args:
            dominant_emotion: The dominant emotion to filter by
            limit: Maximum number of movies
            min_score: Minimum score for the emotion

        Returns:
            List of movies with that dominant emotion
        """
        # Query by dominant emotion
        query = {
            "emotions.dominant_emotion": dominant_emotion
        }

        movies = await self.movies_collection.find(query).sort(
            "vote_average", -1
        ).limit(limit).to_list(length=limit)

        return [{"movie": movie, "similarity_score": 1.0} for movie in movies]

    def _generate_emotions_from_genres(self, movie: Dict) -> Dict:
        """
        Generate emotion profile from movie genres when BERT analysis is not available
        
        Args:
            movie: Movie document with genres
            
        Returns:
            Dictionary of emotions based on genres
        """
        # Genre to emotion mapping
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
        
        # Get genres from movie
        genres = movie.get("genres", [])
        genre_names = [g.get("name", "") if isinstance(g, dict) else g for g in genres]
        
        # Aggregate emotions from all genres
        combined_emotions = {
            "joy": 0.0, "sadness": 0.0, "fear": 0.0, "anger": 0.0,
            "surprise": 0.0, "disgust": 0.0, "thrill": 0.0, 
            "romance": 0.0, "humor": 0.0, "inspiration": 0.0
        }
        
        genre_count = 0
        for genre_name in genre_names:
            if genre_name in genre_emotions:
                genre_count += 1
                for emotion, score in genre_emotions[genre_name].items():
                    combined_emotions[emotion] = max(combined_emotions[emotion], score)
        
        if genre_count == 0:
            # Default neutral emotions
            return {
                "base_emotions": {"joy": 0.3, "sadness": 0.2, "fear": 0.2, "anger": 0.1, "surprise": 0.2, "disgust": 0.1},
                "thrill": 0.2, "romance": 0.2, "humor": 0.2, "inspiration": 0.2,
                "dominant_emotion": "joy"
            }
        
        # Find dominant emotion
        base_emotions = {k: combined_emotions[k] for k in ["joy", "sadness", "fear", "anger", "surprise", "disgust"]}
        dominant = max(base_emotions, key=base_emotions.get)
        
        return {
            "base_emotions": base_emotions,
            "thrill": combined_emotions["thrill"],
            "romance": combined_emotions["romance"],
            "humor": combined_emotions["humor"],
            "inspiration": combined_emotions["inspiration"],
            "dominant_emotion": dominant
        }

    def close(self):
        """Close database connection"""
        self.client.close()


# Singleton instance
_recommendation_service: Optional[RecommendationService] = None


def get_recommendation_service() -> RecommendationService:
    """Get or create recommendation service singleton"""
    global _recommendation_service

    if _recommendation_service is None:
        _recommendation_service = RecommendationService()

    return _recommendation_service
