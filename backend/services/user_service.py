"""
User service for authentication and profile management using Neo4j
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from passlib.context import CryptContext
from jose import JWTError, jwt
from neo4j import GraphDatabase
from config.settings import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def convert_neo4j_types(obj):
    """Convert Neo4j types to Python native types"""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: convert_neo4j_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_neo4j_types(item) for item in obj]
    # Handle Neo4j DateTime
    if hasattr(obj, 'iso_format'):
        return obj.iso_format()
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return obj


class UserService:
    """Service for user management with Neo4j"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.close()

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
        """Create a new user in Neo4j"""
        hashed_password = self.get_password_hash(password)
        user_id = f"user_{datetime.utcnow().timestamp()}"

        with self.driver.session() as session:
            result = session.run(
                """
                CREATE (u:User {
                    user_id: $user_id,
                    email: $email,
                    username: $username,
                    hashed_password: $hashed_password,
                    full_name: $full_name,
                    created_at: datetime()
                })
                RETURN u
                """,
                user_id=user_id,
                email=email,
                username=username,
                hashed_password=hashed_password,
                full_name=full_name
            )
            user = result.single()
            if user:
                return convert_neo4j_types(dict(user["u"]))
        return None

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {email: $email}) RETURN u",
                email=email
            )
            user = result.single()
            if user:
                return convert_neo4j_types(dict(user["u"]))
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user and return user data"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.get("hashed_password")):
            return None
        return user

    # Movie interactions
    async def add_movie_interaction(
        self,
        user_id: str,
        movie_id: int,
        liked: bool,
        rating: Optional[float] = None
    ) -> bool:
        """Record user interaction with a movie"""
        with self.driver.session() as session:
            # Create or update WATCHED relationship
            session.run(
                """
                MATCH (u:User {user_id: $user_id})
                MERGE (m:Movie {movie_id: $movie_id})
                MERGE (u)-[w:WATCHED]->(m)
                SET w.liked = $liked,
                    w.rating = $rating,
                    w.watched_at = datetime()
                """,
                user_id=user_id,
                movie_id=movie_id,
                liked=liked,
                rating=rating
            )
            return True

    async def get_user_liked_movies(self, user_id: str) -> List[int]:
        """Get list of movies user liked"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[w:WATCHED {liked: true}]->(m:Movie)
                RETURN m.movie_id as movie_id
                """,
                user_id=user_id
            )
            return [record["movie_id"] for record in result]

    async def get_user_watched_movies(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get user's watch history"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[w:WATCHED]->(m:Movie)
                RETURN m.movie_id as movie_id,
                       w.liked as liked,
                       w.rating as rating,
                       w.watched_at as watched_at
                ORDER BY w.watched_at DESC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit
            )
            return [convert_neo4j_types(dict(record)) for record in result]

    async def get_user_stats(self, user_id: str) -> dict:
        """Get user statistics"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})
                OPTIONAL MATCH (u)-[w:WATCHED]->(m:Movie)
                RETURN count(w) as total_watched,
                       count(CASE WHEN w.liked = true THEN 1 END) as total_liked,
                       avg(w.rating) as avg_rating
                """,
                user_id=user_id
            )
            stats = result.single()
            if stats:
                return {
                    "total_watched": stats["total_watched"],
                    "total_liked": stats["total_liked"],
                    "avg_rating": stats["avg_rating"]
                }
        return {"total_watched": 0, "total_liked": 0, "avg_rating": None}

    async def get_recommended_movies_for_user(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[int]:
        """Get movie recommendations based on user's liked movies (collaborative filtering)"""
        with self.driver.session() as session:
            # Find similar users who liked the same movies
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[:WATCHED {liked: true}]->(m:Movie)
                MATCH (other:User)-[:WATCHED {liked: true}]->(m)
                WHERE other.user_id <> u.user_id
                WITH other, count(m) as common_likes
                ORDER BY common_likes DESC
                LIMIT 5

                MATCH (other)-[:WATCHED {liked: true}]->(rec:Movie)
                WHERE NOT (u)-[:WATCHED]->(rec)
                RETURN DISTINCT rec.movie_id as movie_id,
                       count(other) as recommendation_score
                ORDER BY recommendation_score DESC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit
            )
            return [record["movie_id"] for record in result]

    async def save_recommendation_history(
        self,
        user_id: str,
        movie_ids: List[int],
        mood: str,
        emotions: Dict[str, float]
    ) -> bool:
        """Save recommendation history for user"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {user_id: $user_id})
                CREATE (r:RecommendationHistory {
                    history_id: randomUUID(),
                    mood: $mood,
                    emotions: $emotions,
                    movie_ids: $movie_ids,
                    created_at: datetime()
                })
                CREATE (u)-[:HAS_HISTORY]->(r)
                """,
                user_id=user_id,
                mood=mood,
                emotions=str(emotions),
                movie_ids=movie_ids
            )
            return True

    async def get_recommendation_history(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get user's recommendation history"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[:HAS_HISTORY]->(r:RecommendationHistory)
                RETURN r.history_id as history_id,
                       r.mood as mood,
                       r.emotions as emotions,
                       r.movie_ids as movie_ids,
                       r.created_at as created_at
                ORDER BY r.created_at DESC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit
            )
            return [convert_neo4j_types(dict(record)) for record in result]

    async def update_user_emotional_profile(
        self,
        user_id: str,
        emotions: Dict[str, float]
    ) -> bool:
        """Update user's emotional profile based on their preferences"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {user_id: $user_id})
                SET u.emotional_profile = $emotions,
                    u.profile_updated_at = datetime()
                """,
                user_id=user_id,
                emotions=str(emotions)
            )
            return True

    async def get_user_emotional_profile(self, user_id: str) -> Dict[str, float]:
        """Get user's emotional profile"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})
                RETURN u.emotional_profile as profile
                """,
                user_id=user_id
            )
            record = result.single()
            if record and record["profile"]:
                import ast
                try:
                    return ast.literal_eval(record["profile"])
                except:
                    return {}
            return {}

    async def add_movie_review(
        self,
        user_id: str,
        movie_id: int,
        review_text: str,
        emotions_detected: Dict[str, float]
    ) -> bool:
        """Add a movie review with emotion analysis"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {user_id: $user_id})
                MERGE (m:Movie {movie_id: $movie_id})
                CREATE (r:Review {
                    review_id: randomUUID(),
                    text: $review_text,
                    emotions: $emotions,
                    created_at: datetime()
                })
                CREATE (u)-[:WROTE]->(r)
                CREATE (r)-[:ABOUT]->(m)
                """,
                user_id=user_id,
                movie_id=movie_id,
                review_text=review_text,
                emotions=str(emotions_detected)
            )
            return True

    async def get_user_reviews(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get user's movie reviews"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[:WROTE]->(r:Review)-[:ABOUT]->(m:Movie)
                RETURN r.review_id as review_id,
                       r.text as text,
                       r.emotions as emotions,
                       r.created_at as created_at,
                       m.movie_id as movie_id
                ORDER BY r.created_at DESC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit
            )
            return [convert_neo4j_types(dict(record)) for record in result]

    # ===== Watchlist Methods =====
    
    async def add_to_watchlist(self, email: str, movie_id: int, title: str,
                               poster_path: str = "", vote_average: float = 0) -> bool:
        """Add a movie to user's watchlist"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})
                MERGE (m:Movie {movie_id: $movie_id})
                ON CREATE SET m.title = $title,
                              m.poster_path = $poster_path,
                              m.vote_average = $vote_average
                MERGE (u)-[r:WANTS_TO_WATCH]->(m)
                ON CREATE SET r.added_at = datetime()
                RETURN m
                """,
                email=email,
                movie_id=movie_id,
                title=title,
                poster_path=poster_path,
                vote_average=vote_average
            )
            return result.single() is not None
    
    async def remove_from_watchlist(self, email: str, movie_id: int) -> bool:
        """Remove a movie from user's watchlist"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})-[r:WANTS_TO_WATCH]->(m:Movie {movie_id: $movie_id})
                DELETE r
                RETURN count(r) as deleted
                """,
                email=email,
                movie_id=movie_id
            )
            record = result.single()
            return record["deleted"] > 0 if record else False
    
    async def get_watchlist(self, email: str) -> List[dict]:
        """Get user's watchlist"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})-[r:WANTS_TO_WATCH]->(m:Movie)
                RETURN m.movie_id as id,
                       m.title as title,
                       m.poster_path as poster_path,
                       m.vote_average as vote_average,
                       r.added_at as added_at
                ORDER BY r.added_at DESC
                """,
                email=email
            )
            return [convert_neo4j_types(dict(record)) for record in result]
    
    async def is_in_watchlist(self, email: str, movie_id: int) -> bool:
        """Check if a movie is in user's watchlist"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})-[:WANTS_TO_WATCH]->(m:Movie {movie_id: $movie_id})
                RETURN count(m) > 0 as exists
                """,
                email=email,
                movie_id=movie_id
            )
            record = result.single()
            return record["exists"] if record else False
    
    async def clear_watchlist(self, email: str) -> int:
        """Clear user's entire watchlist"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})-[r:WANTS_TO_WATCH]->(m:Movie)
                DELETE r
                RETURN count(r) as deleted
                """,
                email=email
            )
            record = result.single()
            return record["deleted"] if record else 0
    
    # ===== Analysis History Methods =====
    
    async def save_analysis(self, email: str, emotions: Dict, movie_count: int) -> Optional[dict]:
        """Save an emotion analysis to user's history"""
        # Convert emotions dict to JSON string (Neo4j doesn't accept Map as property)
        emotions_json = json.dumps(emotions)
        
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})
                CREATE (a:Analysis {
                    id: randomUUID(),
                    emotions_json: $emotions_json,
                    movie_count: $movie_count,
                    created_at: datetime()
                })
                CREATE (u)-[:PERFORMED]->(a)
                RETURN a.id as id, a.emotions_json as emotions_json, 
                       a.movie_count as movie_count, a.created_at as date
                """,
                email=email,
                emotions_json=emotions_json,
                movie_count=movie_count
            )
            record = result.single()
            if record:
                # Update user's aggregate emotion profile
                self._update_aggregate_profile(session, email)
                result_dict = convert_neo4j_types(dict(record))
                # Parse emotions back to dict
                result_dict["emotions"] = json.loads(result_dict.get("emotions_json", "{}"))
                del result_dict["emotions_json"]
                return result_dict
            return None
            return None
    
    def _update_aggregate_profile(self, session, email: str):
        """Update user's aggregate emotion profile based on analysis history"""
        # Get all analyses and compute average in Python (since emotions are stored as JSON string)
        result = session.run(
            """
            MATCH (u:User {email: $email})-[:PERFORMED]->(a:Analysis)
            RETURN a.emotions_json as emotions_json
            """,
            email=email
        )
        
        all_emotions = []
        for record in result:
            emotions_json = record.get("emotions_json")
            if emotions_json:
                try:
                    emotions = json.loads(emotions_json)
                    all_emotions.append(emotions)
                except:
                    pass
        
        if not all_emotions:
            return
            
        # Calculate averages
        emotion_keys = ["joy", "sadness", "fear", "anger", "surprise", "disgust"]
        profile = {}
        for key in emotion_keys:
            values = [e.get(key, 0) for e in all_emotions]
            profile[key] = sum(values) / len(values) if values else 0.0
        
        # Store profile as individual properties (not as Map)
        session.run(
            """
            MATCH (u:User {email: $email})
            SET u.profile_joy = $joy,
                u.profile_sadness = $sadness,
                u.profile_fear = $fear,
                u.profile_anger = $anger,
                u.profile_surprise = $surprise,
                u.profile_disgust = $disgust
            """,
            email=email,
            joy=profile.get("joy", 0.0),
            sadness=profile.get("sadness", 0.0),
            fear=profile.get("fear", 0.0),
            anger=profile.get("anger", 0.0),
            surprise=profile.get("surprise", 0.0),
            disgust=profile.get("disgust", 0.0)
        )
    
    async def get_analysis_history(self, email: str, limit: int = 20) -> List[dict]:
        """Get user's analysis history"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})-[:PERFORMED]->(a:Analysis)
                RETURN a.id as id, a.emotions_json as emotions_json,
                       a.movie_count as movieCount, a.created_at as date
                ORDER BY a.created_at DESC
                LIMIT $limit
                """,
                email=email,
                limit=limit
            )
            analyses = []
            for record in result:
                item = convert_neo4j_types(dict(record))
                # Parse emotions JSON
                if item.get("emotions_json"):
                    try:
                        item["emotions"] = json.loads(item["emotions_json"])
                    except:
                        item["emotions"] = {}
                    del item["emotions_json"]
                else:
                    item["emotions"] = {}
                analyses.append(item)
            return analyses
    
    async def get_emotion_profile(self, email: str) -> Dict:
        """Get user's emotion profile"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})
                RETURN u.profile_joy as joy, u.profile_sadness as sadness,
                       u.profile_fear as fear, u.profile_anger as anger,
                       u.profile_surprise as surprise, u.profile_disgust as disgust
                """,
                email=email
            )
            record = result.single()
            if record:
                return {
                    "joy": record["joy"] or 0.0,
                    "sadness": record["sadness"] or 0.0,
                    "fear": record["fear"] or 0.0,
                    "anger": record["anger"] or 0.0,
                    "surprise": record["surprise"] or 0.0,
                    "disgust": record["disgust"] or 0.0
                }
            return {
                "joy": 0.0, "sadness": 0.0, "fear": 0.0,
                "anger": 0.0, "surprise": 0.0, "disgust": 0.0
            }
    
    async def get_user_stats_by_email(self, email: str) -> dict:
        """Get comprehensive user statistics by email"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})
                OPTIONAL MATCH (u)-[:PERFORMED]->(a:Analysis)
                OPTIONAL MATCH (u)-[:WANTS_TO_WATCH]->(m:Movie)
                WITH u,
                     count(DISTINCT a) as total_analyses,
                     sum(coalesce(a.movie_count, 0)) as total_movies_discovered,
                     count(DISTINCT m) as watchlist_count
                RETURN total_analyses, total_movies_discovered, watchlist_count,
                       u.profile_joy as joy, u.profile_sadness as sadness,
                       u.profile_fear as fear, u.profile_anger as anger,
                       u.profile_surprise as surprise, u.profile_disgust as disgust
                """,
                email=email
            )
            record = result.single()
            if record:
                return {
                    "total_analyses": record["total_analyses"],
                    "total_movies": record["total_movies_discovered"],
                    "watchlist_count": record["watchlist_count"],
                    "emotion_profile": {
                        "joy": record["joy"] or 0.0,
                        "sadness": record["sadness"] or 0.0,
                        "fear": record["fear"] or 0.0,
                        "anger": record["anger"] or 0.0,
                        "surprise": record["surprise"] or 0.0,
                        "disgust": record["disgust"] or 0.0
                    }
                }
            return {
                "total_analyses": 0,
                "total_movies": 0,
                "watchlist_count": 0,
                "emotion_profile": {}
            }


# Singleton instance
_user_service = None

def get_user_service() -> UserService:
    """Get singleton UserService instance"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
