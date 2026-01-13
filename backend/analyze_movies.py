"""
Analyze emotions for all movies in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import GraphDatabase
from services.emotion_service import get_emotion_analyzer
from config.settings import get_settings
import logging

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def analyze_all_movies():
    """Analyze emotions for all movies in MongoDB"""
    print("\n" + "="*70)
    print("🎬 CineFeels - Movie Emotion Analysis")
    print("="*70 + "\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    movies_collection = db.movies

    # Initialize emotion analyzer
    print("📥 Loading BERT model...")
    analyzer = get_emotion_analyzer()
    print("✅ Model loaded!\n")

    # Get all movies
    movies = await movies_collection.find().to_list(length=None)
    total_movies = len(movies)

    print(f"📊 Found {total_movies} movies to analyze\n")

    # Statistics
    stats = {
        "total": total_movies,
        "with_reviews": 0,
        "without_reviews": 0,
        "analyzed": 0,
        "failed": 0
    }

    # Analyze each movie
    for i, movie in enumerate(movies, 1):
        movie_id = movie.get("id")
        title = movie.get("title")

        print(f"\n[{i}/{total_movies}] Analyzing: {title}")
        print("-" * 70)

        try:
            # Get reviews
            reviews = movie.get("reviews", {}).get("results", [])
            review_texts = [r.get("content", "") for r in reviews if r.get("content")]

            if review_texts:
                stats["with_reviews"] += 1
                logger.info(f"  Found {len(review_texts)} reviews")

                # Analyze reviews
                emotion_profile = analyzer.analyze_reviews(review_texts)

                # Store emotion data
                emotion_data = {
                    "base_emotions": emotion_profile.base_emotions.to_dict(),
                    "thrill": emotion_profile.thrill,
                    "romance": emotion_profile.romance,
                    "inspiration": emotion_profile.inspiration,
                    "humor": emotion_profile.humor,
                    "dominant_emotion": emotion_profile.dominant_emotion,
                    "reviews_analyzed": emotion_profile.reviews_analyzed
                }

            else:
                stats["without_reviews"] += 1
                logger.info("  No reviews found, analyzing overview...")

                # Fallback to overview analysis
                overview = movie.get("overview", "")
                if overview:
                    emotions = analyzer.analyze_movie_overview(overview, title)

                    emotion_data = {
                        "base_emotions": emotions.to_dict(),
                        "thrill": (emotions.fear + emotions.surprise) / 2,
                        "romance": emotions.joy,
                        "inspiration": (emotions.joy + emotions.surprise) / 2,
                        "humor": emotions.joy,
                        "dominant_emotion": max(emotions.to_dict(), key=emotions.to_dict().get),
                        "reviews_analyzed": 0,
                        "source": "overview"
                    }
                else:
                    logger.warning("  No overview available, skipping...")
                    stats["failed"] += 1
                    continue

            # Update MongoDB
            await movies_collection.update_one(
                {"id": movie_id},
                {"$set": {"emotions": emotion_data}}
            )

            stats["analyzed"] += 1

            # Print summary
            print(f"  ✅ Dominant: {emotion_data['dominant_emotion'].upper()}")
            print(f"  📊 Thrill: {emotion_data['thrill']:.2f} | "
                  f"Romance: {emotion_data['romance']:.2f} | "
                  f"Inspiration: {emotion_data['inspiration']:.2f}")

        except Exception as e:
            logger.error(f"  ❌ Failed to analyze: {e}")
            stats["failed"] += 1

        # Progress update
        if i % 10 == 0:
            print(f"\n📈 Progress: {i}/{total_movies} ({i/total_movies*100:.1f}%)")
            print(f"   Analyzed: {stats['analyzed']} | Failed: {stats['failed']}")

    client.close()

    # Final statistics
    print("\n" + "="*70)
    print("📊 Analysis Complete - Final Statistics")
    print("="*70)
    print(f"  Total movies:        {stats['total']}")
    print(f"  With reviews:        {stats['with_reviews']}")
    print(f"  Without reviews:     {stats['without_reviews']}")
    print(f"  Successfully analyzed: {stats['analyzed']}")
    print(f"  Failed:              {stats['failed']}")
    print("="*70 + "\n")


async def update_neo4j_emotions():
    """Update Neo4j with emotion data"""
    print("\n" + "="*70)
    print("🕸️  Updating Neo4j with Emotion Data")
    print("="*70 + "\n")

    # Connect to MongoDB
    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    mongo_db = mongo_client[settings.mongodb_db_name]

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )

    # Get all movies with emotions
    movies = await mongo_db.movies.find(
        {"emotions": {"$exists": True}}
    ).to_list(length=None)

    print(f"📊 Found {len(movies)} movies with emotion data\n")

    with neo4j_driver.session() as session:
        for i, movie in enumerate(movies, 1):
            movie_id = movie.get("id")
            emotions = movie.get("emotions", {})

            try:
                # Update movie node with emotion properties
                session.run("""
                    MATCH (m:Movie {id: $movie_id})
                    SET m.dominant_emotion = $dominant_emotion,
                        m.thrill = $thrill,
                        m.romance = $romance,
                        m.inspiration = $inspiration,
                        m.humor = $humor,
                        m.joy = $joy,
                        m.sadness = $sadness,
                        m.fear = $fear,
                        m.anger = $anger,
                        m.surprise = $surprise,
                        m.disgust = $disgust
                """, {
                    "movie_id": movie_id,
                    "dominant_emotion": emotions.get("dominant_emotion"),
                    "thrill": emotions.get("thrill"),
                    "romance": emotions.get("romance"),
                    "inspiration": emotions.get("inspiration"),
                    "humor": emotions.get("humor"),
                    "joy": emotions.get("base_emotions", {}).get("joy", 0),
                    "sadness": emotions.get("base_emotions", {}).get("sadness", 0),
                    "fear": emotions.get("base_emotions", {}).get("fear", 0),
                    "anger": emotions.get("base_emotions", {}).get("anger", 0),
                    "surprise": emotions.get("base_emotions", {}).get("surprise", 0),
                    "disgust": emotions.get("base_emotions", {}).get("disgust", 0)
                })

                if i % 20 == 0:
                    print(f"  Updated {i}/{len(movies)} movies...")

            except Exception as e:
                logger.error(f"  Failed to update movie {movie_id}: {e}")

    neo4j_driver.close()
    mongo_client.close()

    print(f"\n✅ Updated {len(movies)} movies in Neo4j\n")


async def show_emotion_distribution():
    """Show emotion distribution across all movies"""
    print("\n" + "="*70)
    print("📊 Emotion Distribution Analysis")
    print("="*70 + "\n")

    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    # Get emotion distribution
    pipeline = [
        {"$match": {"emotions": {"$exists": True}}},
        {"$group": {
            "_id": "$emotions.dominant_emotion",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]

    results = await db.movies.aggregate(pipeline).to_list(length=None)

    print("Dominant Emotions:")
    for result in results:
        emotion = result["_id"]
        count = result["count"]
        bar = "█" * count
        print(f"  {emotion.capitalize():12} {count:3} {bar}")

    # Get average CineFeels emotions
    print("\n\nAverage CineFeels Emotions:")

    avg_pipeline = [
        {"$match": {"emotions": {"$exists": True}}},
        {"$group": {
            "_id": None,
            "avg_thrill": {"$avg": "$emotions.thrill"},
            "avg_romance": {"$avg": "$emotions.romance"},
            "avg_inspiration": {"$avg": "$emotions.inspiration"},
            "avg_humor": {"$avg": "$emotions.humor"}
        }}
    ]

    avg_results = await db.movies.aggregate(avg_pipeline).to_list(length=1)

    if avg_results:
        avg = avg_results[0]
        print(f"  Thrill:       {avg['avg_thrill']:.3f}")
        print(f"  Romance:      {avg['avg_romance']:.3f}")
        print(f"  Inspiration:  {avg['avg_inspiration']:.3f}")
        print(f"  Humor:        {avg['avg_humor']:.3f}")

    client.close()
    print()


async def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--skip-analysis":
        print("⏩ Skipping analysis, updating Neo4j only...")
        await update_neo4j_emotions()
        await show_emotion_distribution()
    else:
        # Analyze all movies
        await analyze_all_movies()

        # Update Neo4j
        await update_neo4j_emotions()

        # Show distribution
        await show_emotion_distribution()

    print("="*70)
    print("✨ All done! Emotions analyzed and stored!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
