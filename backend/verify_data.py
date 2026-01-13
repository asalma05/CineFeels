"""
Verify data in MongoDB and Neo4j databases
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import GraphDatabase
from config.settings import get_settings

settings = get_settings()


async def verify_mongodb():
    """Verify MongoDB data"""
    print("\n" + "="*60)
    print("📦 MongoDB Data Verification")
    print("="*60 + "\n")

    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    # Count movies
    movie_count = await db.movies.count_documents({})
    print(f"📊 Total movies: {movie_count}")

    # Get sample movies
    print(f"\n🎬 Sample movies:")
    movies = await db.movies.find().limit(5).to_list(length=5)

    for i, movie in enumerate(movies, 1):
        print(f"\n{i}. {movie.get('title')} ({movie.get('release_date', 'N/A')[:4]})")
        print(f"   ID: {movie.get('id')}")
        print(f"   Rating: {movie.get('vote_average')}/10")
        print(f"   Genres: {', '.join([g['name'] for g in movie.get('genres', [])])}")
        print(f"   Overview: {movie.get('overview', 'N/A')[:100]}...")

        # Check for reviews
        reviews = movie.get('reviews', {}).get('results', [])
        print(f"   Reviews: {len(reviews)} available")

        # Check for cast
        cast = movie.get('credits', {}).get('cast', [])
        if cast:
            actors = ', '.join([actor['name'] for actor in cast[:3]])
            print(f"   Cast: {actors}")

    client.close()


def verify_neo4j():
    """Verify Neo4j graph data"""
    print("\n" + "="*60)
    print("🕸️  Neo4j Graph Verification")
    print("="*60 + "\n")

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )

    with driver.session() as session:
        # Count nodes by type
        print("📊 Node counts by type:")

        for label in ["Movie", "Genre", "Actor", "Director"]:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
            count = result.single()["count"]
            print(f"   {label}: {count}")

        # Count relationships
        print("\n📊 Relationship counts:")
        for rel_type in ["HAS_GENRE", "ACTED_IN", "DIRECTED"]:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count")
            count = result.single()["count"]
            print(f"   {rel_type}: {count}")

        # Sample movie with relationships
        print("\n🎬 Sample movie graph:")
        result = session.run("""
            MATCH (m:Movie)
            OPTIONAL MATCH (m)-[:HAS_GENRE]->(g:Genre)
            OPTIONAL MATCH (a:Actor)-[:ACTED_IN]->(m)
            OPTIONAL MATCH (d:Director)-[:DIRECTED]->(m)
            WITH m,
                 collect(DISTINCT g.name) AS genres,
                 collect(DISTINCT a.name)[..3] AS actors,
                 collect(DISTINCT d.name) AS directors
            RETURN m.title AS title,
                   m.release_date AS release_date,
                   m.vote_average AS rating,
                   genres,
                   actors,
                   directors
            LIMIT 3
        """)

        for i, record in enumerate(result, 1):
            print(f"\n{i}. {record['title']} ({record['release_date'][:4] if record['release_date'] else 'N/A'})")
            print(f"   Rating: {record['rating']}/10")
            print(f"   Genres: {', '.join(record['genres'])}")
            print(f"   Directors: {', '.join(record['directors'])}")
            print(f"   Top Actors: {', '.join(record['actors'])}")

        # Find movies by genre
        print("\n🎭 Action movies:")
        result = session.run("""
            MATCH (m:Movie)-[:HAS_GENRE]->(g:Genre {name: 'Action'})
            RETURN m.title AS title, m.vote_average AS rating
            ORDER BY m.vote_average DESC
            LIMIT 5
        """)

        for record in result:
            print(f"   • {record['title']} - {record['rating']}/10")

    driver.close()


async def main():
    """Main verification function"""
    print("\n" + "="*60)
    print("🔍 CineFeels - Database Verification")
    print("="*60)

    await verify_mongodb()
    verify_neo4j()

    print("\n" + "="*60)
    print("✅ Verification complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
