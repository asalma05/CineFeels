"""
Import movies with emotion profiles into local MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# TMDB API configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# MongoDB local configuration
MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "cinefeels"

# Emotion profiles for different genres/movies
EMOTION_PROFILES = {
    "Action": {"thrill": 0.85, "joy": 0.4, "fear": 0.3, "sadness": 0.1, "surprise": 0.6, "humor": 0.2},
    "Adventure": {"thrill": 0.7, "joy": 0.65, "fear": 0.25, "sadness": 0.15, "surprise": 0.55, "humor": 0.3},
    "Animation": {"joy": 0.8, "humor": 0.7, "sadness": 0.3, "thrill": 0.4, "surprise": 0.5, "fear": 0.1},
    "Comedy": {"humor": 0.9, "joy": 0.85, "sadness": 0.1, "thrill": 0.2, "surprise": 0.4, "fear": 0.05},
    "Crime": {"thrill": 0.8, "fear": 0.5, "sadness": 0.45, "joy": 0.15, "surprise": 0.6, "humor": 0.1},
    "Documentary": {"sadness": 0.4, "joy": 0.3, "surprise": 0.5, "thrill": 0.35, "fear": 0.2, "humor": 0.15},
    "Drama": {"sadness": 0.7, "joy": 0.35, "thrill": 0.3, "fear": 0.25, "surprise": 0.35, "humor": 0.1},
    "Family": {"joy": 0.85, "humor": 0.7, "sadness": 0.25, "thrill": 0.3, "surprise": 0.45, "fear": 0.1},
    "Fantasy": {"thrill": 0.6, "joy": 0.55, "surprise": 0.7, "fear": 0.35, "sadness": 0.25, "humor": 0.3},
    "History": {"sadness": 0.55, "thrill": 0.45, "joy": 0.25, "fear": 0.35, "surprise": 0.4, "humor": 0.1},
    "Horror": {"fear": 0.95, "thrill": 0.85, "surprise": 0.7, "sadness": 0.4, "joy": 0.05, "humor": 0.1},
    "Music": {"joy": 0.8, "sadness": 0.4, "thrill": 0.35, "humor": 0.45, "surprise": 0.3, "fear": 0.05},
    "Mystery": {"thrill": 0.8, "surprise": 0.85, "fear": 0.55, "sadness": 0.35, "joy": 0.2, "humor": 0.1},
    "Romance": {"joy": 0.75, "sadness": 0.55, "thrill": 0.25, "humor": 0.4, "surprise": 0.35, "fear": 0.1},
    "Science Fiction": {"thrill": 0.75, "surprise": 0.8, "fear": 0.45, "joy": 0.4, "sadness": 0.3, "humor": 0.2},
    "TV Movie": {"joy": 0.5, "sadness": 0.4, "thrill": 0.3, "humor": 0.45, "surprise": 0.35, "fear": 0.15},
    "Thriller": {"thrill": 0.95, "fear": 0.75, "surprise": 0.8, "sadness": 0.4, "joy": 0.1, "humor": 0.05},
    "War": {"sadness": 0.8, "fear": 0.7, "thrill": 0.75, "joy": 0.1, "surprise": 0.45, "humor": 0.05},
    "Western": {"thrill": 0.7, "joy": 0.35, "sadness": 0.4, "fear": 0.3, "surprise": 0.45, "humor": 0.25}
}


def generate_emotion_profile(genres):
    """Generate emotion profile based on movie genres"""
    if not genres:
        return {
            "thrill": 0.5, "joy": 0.5, "sadness": 0.5,
            "fear": 0.5, "surprise": 0.5, "humor": 0.5
        }

    # Average emotions across all genres
    emotions = {"thrill": 0, "joy": 0, "sadness": 0, "fear": 0, "surprise": 0, "humor": 0}
    count = 0

    for genre in genres:
        genre_name = genre.get("name", "")
        if genre_name in EMOTION_PROFILES:
            profile = EMOTION_PROFILES[genre_name]
            for emotion, value in profile.items():
                emotions[emotion] += value
            count += 1

    if count > 0:
        for emotion in emotions:
            emotions[emotion] = round(emotions[emotion] / count, 2)

    # Determine dominant emotion
    dominant = max(emotions, key=emotions.get)

    return {
        **emotions,
        "dominant_emotion": dominant
    }


async def fetch_popular_movies(page=1):
    """Fetch popular movies from TMDB"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TMDB_BASE_URL}/movie/popular",
            headers={"Authorization": f"Bearer {TMDB_API_KEY}"},
            params={"page": page, "language": "en-US"}
        )
        if response.status_code == 200:
            return response.json().get("results", [])
        return []


async def fetch_movie_details(movie_id):
    """Fetch detailed movie information"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}",
            headers={"Authorization": f"Bearer {TMDB_API_KEY}"},
            params={"language": "en-US", "append_to_response": "credits,keywords"}
        )
        if response.status_code == 200:
            return response.json()
        return None


async def import_movies():
    """Main import function"""
    print("🎬 CineFeels - Movie Import Script")
    print("=" * 50)

    # Connect to MongoDB local
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    movies_collection = db.movies

    # Check existing count
    existing = await movies_collection.count_documents({})
    print(f"📊 Existing movies in database: {existing}")

    if existing >= 100:
        print("✅ Database already has 100+ movies. Skipping import.")
        client.close()
        return

    print(f"📥 Importing movies from TMDB...")

    all_movies = []

    # Fetch 5 pages of popular movies (100 movies)
    for page in range(1, 6):
        print(f"   Fetching page {page}/5...")
        movies = await fetch_popular_movies(page)
        all_movies.extend(movies)
        await asyncio.sleep(0.3)  # Rate limiting

    print(f"📦 Fetched {len(all_movies)} movies, processing details...")

    imported = 0
    for i, movie in enumerate(all_movies):
        movie_id = movie["id"]

        # Check if already exists
        exists = await movies_collection.find_one({"id": movie_id})
        if exists:
            continue

        # Fetch full details
        details = await fetch_movie_details(movie_id)
        if not details:
            continue

        # Generate emotion profile
        emotions = generate_emotion_profile(details.get("genres", []))

        # Prepare movie document
        movie_doc = {
            "id": movie_id,
            "title": details.get("title", "Unknown"),
            "original_title": details.get("original_title"),
            "overview": details.get("overview", ""),
            "release_date": details.get("release_date"),
            "genres": details.get("genres", []),
            "vote_average": details.get("vote_average", 0),
            "vote_count": details.get("vote_count", 0),
            "popularity": details.get("popularity", 0),
            "poster_path": details.get("poster_path"),
            "backdrop_path": details.get("backdrop_path"),
            "runtime": details.get("runtime"),
            "budget": details.get("budget"),
            "revenue": details.get("revenue"),
            "tagline": details.get("tagline"),
            "status": details.get("status"),
            "emotions": emotions,
            "production_companies": details.get("production_companies", []),
            "production_countries": details.get("production_countries", []),
            "spoken_languages": details.get("spoken_languages", [])
        }

        # Add cast info if available
        credits = details.get("credits", {})
        if credits:
            cast = credits.get("cast", [])[:10]  # Top 10 actors
            crew = credits.get("crew", [])
            directors = [c for c in crew if c.get("job") == "Director"]

            movie_doc["cast"] = [{"id": c["id"], "name": c["name"], "character": c.get("character")} for c in cast]
            movie_doc["directors"] = [{"id": d["id"], "name": d["name"]} for d in directors]

        # Insert into MongoDB
        await movies_collection.insert_one(movie_doc)
        imported += 1

        if imported % 10 == 0:
            print(f"   Imported {imported} movies...")

        await asyncio.sleep(0.2)  # Rate limiting

    # Final count
    final_count = await movies_collection.count_documents({})
    print(f"\n✅ Import complete!")
    print(f"📊 Total movies in database: {final_count}")
    print(f"📊 Movies with emotions: {final_count}")

    # Show emotion distribution
    pipeline = [
        {"$match": {"emotions": {"$exists": True}}},
        {"$group": {"_id": "$emotions.dominant_emotion", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    emotion_dist = await movies_collection.aggregate(pipeline).to_list(length=None)

    print(f"\n📈 Emotion Distribution:")
    for e in emotion_dist:
        print(f"   {e['_id']}: {e['count']} movies")

    client.close()
    print("\n🎉 Database ready!")


if __name__ == "__main__":
    asyncio.run(import_movies())
