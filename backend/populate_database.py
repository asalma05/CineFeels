"""
Populate MongoDB and Neo4j with movie data from TMDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import GraphDatabase
from services.tmdb_service import TMDBService
from config.settings import get_settings

settings = get_settings()


class DatabasePopulator:
    """Populate databases with TMDB data"""

    def __init__(self):
        self.tmdb_service = TMDBService()
        self.mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
        self.mongo_db = self.mongo_client[settings.mongodb_db_name]
        self.neo4j_driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    async def populate_mongodb(self, num_pages: int = 5):
        """
        Populate MongoDB with movie data

        Args:
            num_pages: Number of pages of popular movies to fetch
        """
        print(f"\n📦 Populating MongoDB with movies...")
        movies_collection = self.mongo_db.movies

        all_movies = []
        seen_ids = set()  # Track IDs to avoid duplicates

        for page in range(1, num_pages + 1):
            print(f"   📥 Fetching page {page}/{num_pages}...")
            data = await self.tmdb_service.get_popular_movies(page=page)
            movies = data.get("results", [])

            # Fetch detailed info for each movie
            for movie in movies:
                movie_id = movie["id"]

                # Skip if we've already seen this movie
                if movie_id in seen_ids:
                    continue

                try:
                    details = await self.tmdb_service.get_movie_details(movie_id)
                    all_movies.append(details)
                    seen_ids.add(movie_id)
                except Exception as e:
                    print(f"      ⚠️  Failed to fetch details for movie {movie_id}: {e}")

        # Insert movies into MongoDB
        if all_movies:
            print(f"\n   💾 Inserting {len(all_movies)} movies into MongoDB...")

            # Clear existing data and drop all indexes
            await movies_collection.drop()
            print(f"   🧹 Cleared existing data and indexes")

            await movies_collection.insert_many(all_movies)
            print(f"   ✅ Successfully inserted {len(all_movies)} movies")

            # Create index on movie ID
            try:
                await movies_collection.create_index("id", unique=True)
                print(f"   📇 Created index on movie ID")
            except Exception as e:
                print(f"   ⚠️  Index creation warning: {e}")
        else:
            print(f"   ⚠️  No movies to insert")

    async def populate_neo4j(self):
        """
        Populate Neo4j with movie graph data
        """
        print(f"\n🕸️  Populating Neo4j with movie graph...")

        with self.neo4j_driver.session() as session:
            # Clear existing data
            print(f"   🧹 Clearing existing graph data...")
            session.run("MATCH (n) DETACH DELETE n")

            # Fetch movies from MongoDB
            print(f"   📥 Fetching movies from MongoDB...")

            # Get movies from MongoDB
            movies = await self.mongo_db.movies.find().to_list(length=None)

            print(f"   📊 Creating {len(movies)} movie nodes...")

            # Create Movie nodes
            for movie in movies:
                session.run("""
                    CREATE (m:Movie {
                        id: $id,
                        title: $title,
                        overview: $overview,
                        release_date: $release_date,
                        vote_average: $vote_average,
                        popularity: $popularity,
                        poster_path: $poster_path
                    })
                """, {
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "overview": movie.get("overview"),
                    "release_date": movie.get("release_date"),
                    "vote_average": movie.get("vote_average"),
                    "popularity": movie.get("popularity"),
                    "poster_path": movie.get("poster_path")
                })

                # Create Genre nodes and relationships
                for genre in movie.get("genres", []):
                    session.run("""
                        MERGE (g:Genre {id: $genre_id, name: $genre_name})
                        WITH g
                        MATCH (m:Movie {id: $movie_id})
                        MERGE (m)-[:HAS_GENRE]->(g)
                    """, {
                        "genre_id": genre["id"],
                        "genre_name": genre["name"],
                        "movie_id": movie.get("id")
                    })

                # Create Actor nodes and relationships
                credits = movie.get("credits", {})
                cast = credits.get("cast", [])[:10]  # Top 10 actors
                for actor in cast:
                    session.run("""
                        MERGE (a:Actor {id: $actor_id, name: $actor_name})
                        WITH a
                        MATCH (m:Movie {id: $movie_id})
                        MERGE (a)-[:ACTED_IN {character: $character}]->(m)
                    """, {
                        "actor_id": actor.get("id"),
                        "actor_name": actor.get("name"),
                        "character": actor.get("character"),
                        "movie_id": movie.get("id")
                    })

                # Create Director nodes and relationships
                crew = credits.get("crew", [])
                directors = [c for c in crew if c.get("job") == "Director"]
                for director in directors:
                    session.run("""
                        MERGE (d:Director {id: $director_id, name: $director_name})
                        WITH d
                        MATCH (m:Movie {id: $movie_id})
                        MERGE (d)-[:DIRECTED]->(m)
                    """, {
                        "director_id": director.get("id"),
                        "director_name": director.get("name"),
                        "movie_id": movie.get("id")
                    })

            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()["count"]
            print(f"   ✅ Created {count} total nodes in graph")

    def close(self):
        """Close database connections"""
        self.mongo_client.close()
        self.neo4j_driver.close()


async def main():
    """Main function to populate databases"""
    print("\n" + "="*60)
    print("🎬 CineFeels - Database Population")
    print("="*60)

    populator = DatabasePopulator()

    try:
        # Populate MongoDB
        await populator.populate_mongodb(num_pages=5)

        # Populate Neo4j
        await populator.populate_neo4j()

        print("\n" + "="*60)
        print("✨ Database population complete! 🚀")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Population failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        populator.close()


if __name__ == "__main__":
    asyncio.run(main())
