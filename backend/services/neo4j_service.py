"""
Neo4j Database Service for CineFeels
Handles all Neo4j database operations for users, analyses, and watchlists
"""

from neo4j import GraphDatabase
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = None
        self.uri = uri
        self.user = user
        self.password = password
        
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j")
            self.setup_constraints()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def setup_constraints(self):
        """Set up database constraints and indexes"""
        with self.driver.session() as session:
            # User constraints
            session.run("""
                CREATE CONSTRAINT user_email IF NOT EXISTS
                FOR (u:User) REQUIRE u.email IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT user_username IF NOT EXISTS
                FOR (u:User) REQUIRE u.username IS UNIQUE
            """)
            # Movie constraint
            session.run("""
                CREATE CONSTRAINT movie_id IF NOT EXISTS
                FOR (m:Movie) REQUIRE m.tmdb_id IS UNIQUE
            """)
            logger.info("Neo4j constraints created")
    
    # ===== User Operations =====
    
    def create_user(self, email: str, username: str, hashed_password: str, 
                    full_name: str = "") -> Optional[Dict]:
        """Create a new user in Neo4j"""
        with self.driver.session() as session:
            result = session.run("""
                CREATE (u:User {
                    email: $email,
                    username: $username,
                    hashed_password: $hashed_password,
                    full_name: $full_name,
                    created_at: datetime(),
                    emotion_profile: $emotion_profile
                })
                RETURN u
            """, 
                email=email,
                username=username,
                hashed_password=hashed_password,
                full_name=full_name,
                emotion_profile={
                    "joy": 0.0, "sadness": 0.0, "fear": 0.0,
                    "anger": 0.0, "surprise": 0.0, "disgust": 0.0
                }
            )
            record = result.single()
            if record:
                return dict(record["u"])
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})
                RETURN u
            """, email=email)
            record = result.single()
            if record:
                return dict(record["u"])
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {username: $username})
                RETURN u
            """, username=username)
            record = result.single()
            if record:
                return dict(record["u"])
            return None
    
    def update_emotion_profile(self, email: str, emotion_profile: Dict) -> bool:
        """Update user's emotion profile"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})
                SET u.emotion_profile = $emotion_profile
                RETURN u
            """, email=email, emotion_profile=emotion_profile)
            return result.single() is not None
    
    def get_emotion_profile(self, email: str) -> Optional[Dict]:
        """Get user's emotion profile"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})
                RETURN u.emotion_profile as profile
            """, email=email)
            record = result.single()
            if record:
                return record["profile"]
            return None
    
    # ===== Analysis History Operations =====
    
    def save_analysis(self, email: str, emotions: Dict, movie_count: int) -> Optional[Dict]:
        """Save an emotion analysis to user's history"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})
                CREATE (a:Analysis {
                    id: randomUUID(),
                    emotions: $emotions,
                    movie_count: $movie_count,
                    created_at: datetime()
                })
                CREATE (u)-[:PERFORMED]->(a)
                RETURN a
            """, email=email, emotions=emotions, movie_count=movie_count)
            record = result.single()
            if record:
                analysis = dict(record["a"])
                # Update user's emotion profile (aggregate)
                self._update_aggregate_profile(session, email)
                return analysis
            return None
    
    def _update_aggregate_profile(self, session, email: str):
        """Update user's aggregate emotion profile based on analysis history"""
        result = session.run("""
            MATCH (u:User {email: $email})-[:PERFORMED]->(a:Analysis)
            WITH u, collect(a.emotions) as all_emotions
            WITH u, all_emotions,
                 reduce(s = 0.0, e IN all_emotions | s + coalesce(e.joy, 0)) / size(all_emotions) as avg_joy,
                 reduce(s = 0.0, e IN all_emotions | s + coalesce(e.sadness, 0)) / size(all_emotions) as avg_sadness,
                 reduce(s = 0.0, e IN all_emotions | s + coalesce(e.fear, 0)) / size(all_emotions) as avg_fear,
                 reduce(s = 0.0, e IN all_emotions | s + coalesce(e.anger, 0)) / size(all_emotions) as avg_anger,
                 reduce(s = 0.0, e IN all_emotions | s + coalesce(e.surprise, 0)) / size(all_emotions) as avg_surprise,
                 reduce(s = 0.0, e IN all_emotions | s + coalesce(e.disgust, 0)) / size(all_emotions) as avg_disgust
            SET u.emotion_profile = {
                joy: avg_joy,
                sadness: avg_sadness,
                fear: avg_fear,
                anger: avg_anger,
                surprise: avg_surprise,
                disgust: avg_disgust
            }
            RETURN u
        """, email=email)
    
    def get_analysis_history(self, email: str, limit: int = 20) -> List[Dict]:
        """Get user's analysis history"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})-[:PERFORMED]->(a:Analysis)
                RETURN a
                ORDER BY a.created_at DESC
                LIMIT $limit
            """, email=email, limit=limit)
            return [dict(record["a"]) for record in result]
    
    def get_analysis_count(self, email: str) -> int:
        """Get count of user's analyses"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})-[:PERFORMED]->(a:Analysis)
                RETURN count(a) as count
            """, email=email)
            record = result.single()
            return record["count"] if record else 0
    
    # ===== Watchlist Operations =====
    
    def add_to_watchlist(self, email: str, movie_id: int, title: str, 
                         poster_path: str = "", vote_average: float = 0) -> bool:
        """Add a movie to user's watchlist"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})
                MERGE (m:Movie {tmdb_id: $movie_id})
                ON CREATE SET m.title = $title, 
                              m.poster_path = $poster_path,
                              m.vote_average = $vote_average
                MERGE (u)-[r:WANTS_TO_WATCH]->(m)
                ON CREATE SET r.added_at = datetime()
                RETURN m
            """, email=email, movie_id=movie_id, title=title, 
                 poster_path=poster_path, vote_average=vote_average)
            return result.single() is not None
    
    def remove_from_watchlist(self, email: str, movie_id: int) -> bool:
        """Remove a movie from user's watchlist"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})-[r:WANTS_TO_WATCH]->(m:Movie {tmdb_id: $movie_id})
                DELETE r
                RETURN count(r) as deleted
            """, email=email, movie_id=movie_id)
            record = result.single()
            return record["deleted"] > 0 if record else False
    
    def get_watchlist(self, email: str) -> List[Dict]:
        """Get user's watchlist"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})-[r:WANTS_TO_WATCH]->(m:Movie)
                RETURN m, r.added_at as added_at
                ORDER BY r.added_at DESC
            """, email=email)
            watchlist = []
            for record in result:
                movie = dict(record["m"])
                movie["id"] = movie.pop("tmdb_id", None)
                movie["added_at"] = str(record["added_at"]) if record["added_at"] else None
                watchlist.append(movie)
            return watchlist
    
    def is_in_watchlist(self, email: str, movie_id: int) -> bool:
        """Check if a movie is in user's watchlist"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})-[:WANTS_TO_WATCH]->(m:Movie {tmdb_id: $movie_id})
                RETURN count(m) > 0 as exists
            """, email=email, movie_id=movie_id)
            record = result.single()
            return record["exists"] if record else False
    
    def clear_watchlist(self, email: str) -> int:
        """Clear user's entire watchlist"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})-[r:WANTS_TO_WATCH]->(m:Movie)
                DELETE r
                RETURN count(r) as deleted
            """, email=email)
            record = result.single()
            return record["deleted"] if record else 0
    
    def get_watchlist_count(self, email: str) -> int:
        """Get count of movies in watchlist"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})-[:WANTS_TO_WATCH]->(m:Movie)
                RETURN count(m) as count
            """, email=email)
            record = result.single()
            return record["count"] if record else 0
    
    # ===== Statistics =====
    
    def get_user_stats(self, email: str) -> Dict:
        """Get all user statistics"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})
                OPTIONAL MATCH (u)-[:PERFORMED]->(a:Analysis)
                OPTIONAL MATCH (u)-[:WANTS_TO_WATCH]->(m:Movie)
                WITH u, 
                     count(DISTINCT a) as total_analyses,
                     sum(coalesce(a.movie_count, 0)) as total_movies_discovered,
                     count(DISTINCT m) as watchlist_count
                RETURN {
                    total_analyses: total_analyses,
                    total_movies: total_movies_discovered,
                    watchlist_count: watchlist_count,
                    emotion_profile: u.emotion_profile
                } as stats
            """, email=email)
            record = result.single()
            if record:
                return record["stats"]
            return {
                "total_analyses": 0,
                "total_movies": 0,
                "watchlist_count": 0,
                "emotion_profile": {}
            }


# Singleton instance
_neo4j_service: Optional[Neo4jService] = None


def get_neo4j_service() -> Neo4jService:
    """Get or create Neo4j service instance"""
    global _neo4j_service
    if _neo4j_service is None:
        from config.settings import get_settings
        settings = get_settings()
        _neo4j_service = Neo4jService(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        _neo4j_service.connect()
    return _neo4j_service


def init_neo4j():
    """Initialize Neo4j connection on app startup"""
    service = get_neo4j_service()
    return service.driver is not None
