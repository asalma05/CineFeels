"""
Interactive MongoDB Explorer for CineFeels
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import get_settings
import json

settings = get_settings()


async def show_stats():
    """Show database statistics"""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    print("\n" + "="*70)
    print("📊 MongoDB Statistics")
    print("="*70 + "\n")

    # Count movies
    movie_count = await db.movies.count_documents({})
    print(f"Total movies: {movie_count}")

    # Count movies with reviews
    movies_with_reviews = await db.movies.count_documents({
        "reviews.results": {"$exists": True, "$ne": []}
    })
    print(f"Movies with reviews: {movies_with_reviews}")

    # Genre distribution
    print("\n📊 Genre Distribution:")
    pipeline = [
        {"$unwind": "$genres"},
        {"$group": {"_id": "$genres.name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    genres = await db.movies.aggregate(pipeline).to_list(length=10)
    for genre in genres:
        print(f"   {genre['_id']}: {genre['count']} films")

    # Rating distribution
    print("\n⭐ Rating Distribution:")
    pipeline = [
        {"$bucket": {
            "groupBy": "$vote_average",
            "boundaries": [0, 5, 6, 7, 8, 9, 10],
            "default": "Other",
            "output": {"count": {"$sum": 1}}
        }}
    ]
    ratings = await db.movies.aggregate(pipeline).to_list(length=10)
    for rating in ratings:
        boundary = rating['_id']
        if boundary != "Other":
            print(f"   {boundary}-{boundary+1}: {rating['count']} films")
        else:
            print(f"   Other: {rating['count']} films")

    client.close()


async def search_movies(query: str):
    """Search movies by title"""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    print(f"\n🔍 Searching for: '{query}'")
    print("="*70 + "\n")

    movies = await db.movies.find({
        "title": {"$regex": query, "$options": "i"}
    }).to_list(length=10)

    if not movies:
        print("No movies found.")
    else:
        for i, movie in enumerate(movies, 1):
            print(f"{i}. {movie['title']} ({movie.get('release_date', 'N/A')[:4]})")
            print(f"   Rating: {movie.get('vote_average')}/10")
            print(f"   Genres: {', '.join([g['name'] for g in movie.get('genres', [])])}")
            print()

    client.close()


async def show_movie_details(movie_title: str):
    """Show detailed information about a movie"""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    movie = await db.movies.find_one({
        "title": {"$regex": f"^{movie_title}$", "$options": "i"}
    })

    if not movie:
        print(f"\n❌ Movie '{movie_title}' not found.")
        client.close()
        return

    print("\n" + "="*70)
    print(f"🎬 {movie['title']}")
    print("="*70 + "\n")

    print(f"ID: {movie['id']}")
    print(f"Release Date: {movie.get('release_date', 'N/A')}")
    print(f"Rating: {movie.get('vote_average')}/10 ({movie.get('vote_count')} votes)")
    print(f"Runtime: {movie.get('runtime', 'N/A')} minutes")
    print(f"Budget: ${movie.get('budget', 0):,}")
    print(f"Revenue: ${movie.get('revenue', 0):,}")

    print(f"\nGenres: {', '.join([g['name'] for g in movie.get('genres', [])])}")

    print(f"\nOverview:")
    print(f"{movie.get('overview', 'N/A')}")

    # Cast
    cast = movie.get('credits', {}).get('cast', [])[:5]
    if cast:
        print(f"\nTop Cast:")
        for actor in cast:
            print(f"   • {actor['name']} as {actor.get('character', 'N/A')}")

    # Directors
    crew = movie.get('credits', {}).get('crew', [])
    directors = [c for c in crew if c.get('job') == 'Director']
    if directors:
        print(f"\nDirectors:")
        for director in directors:
            print(f"   • {director['name']}")

    # Reviews
    reviews = movie.get('reviews', {}).get('results', [])
    print(f"\nReviews: {len(reviews)} available")
    if reviews:
        print(f"\nSample Review:")
        review = reviews[0]
        print(f"   Author: {review.get('author', 'Anonymous')}")
        print(f"   Rating: {review.get('author_details', {}).get('rating', 'N/A')}/10")
        content = review.get('content', '')[:200]
        print(f"   {content}...")

    # Keywords
    keywords = movie.get('keywords', {}).get('keywords', [])
    if keywords:
        keyword_names = [k['name'] for k in keywords[:10]]
        print(f"\nKeywords: {', '.join(keyword_names)}")

    client.close()


async def show_top_movies(limit: int = 10):
    """Show top rated movies"""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    print(f"\n⭐ Top {limit} Rated Movies")
    print("="*70 + "\n")

    movies = await db.movies.find().sort("vote_average", -1).limit(limit).to_list(length=limit)

    for i, movie in enumerate(movies, 1):
        print(f"{i}. {movie['title']} ({movie.get('release_date', 'N/A')[:4]})")
        print(f"   Rating: {movie.get('vote_average')}/10 ({movie.get('vote_count')} votes)")
        genres = ', '.join([g['name'] for g in movie.get('genres', [])])
        print(f"   Genres: {genres}")
        print()

    client.close()


async def show_movies_by_genre(genre: str):
    """Show movies by genre"""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    print(f"\n🎭 {genre} Movies")
    print("="*70 + "\n")

    movies = await db.movies.find({
        "genres.name": {"$regex": f"^{genre}$", "$options": "i"}
    }).sort("vote_average", -1).limit(10).to_list(length=10)

    if not movies:
        print(f"No {genre} movies found.")
    else:
        for i, movie in enumerate(movies, 1):
            print(f"{i}. {movie['title']} ({movie.get('release_date', 'N/A')[:4]})")
            print(f"   Rating: {movie.get('vote_average')}/10")
            print()

    client.close()


async def export_to_json(movie_title: str, output_file: str = "movie_export.json"):
    """Export a movie to JSON file"""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    movie = await db.movies.find_one({
        "title": {"$regex": f"^{movie_title}$", "$options": "i"}
    })

    if not movie:
        print(f"\n❌ Movie '{movie_title}' not found.")
        client.close()
        return

    # Remove MongoDB _id field
    movie.pop('_id', None)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(movie, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Movie exported to {output_file}")

    client.close()


async def interactive_menu():
    """Interactive menu for exploring MongoDB"""
    while True:
        print("\n" + "="*70)
        print("🎬 CineFeels MongoDB Explorer")
        print("="*70)
        print("\nOptions:")
        print("1. Show database statistics")
        print("2. Search movies by title")
        print("3. Show top rated movies")
        print("4. Show movies by genre")
        print("5. Show movie details")
        print("6. Export movie to JSON")
        print("0. Exit")

        choice = input("\nEnter your choice (0-6): ").strip()

        if choice == "0":
            print("\n👋 Goodbye!\n")
            break
        elif choice == "1":
            await show_stats()
        elif choice == "2":
            query = input("Enter search query: ").strip()
            await search_movies(query)
        elif choice == "3":
            limit = input("How many movies to show? (default: 10): ").strip()
            limit = int(limit) if limit else 10
            await show_top_movies(limit)
        elif choice == "4":
            genre = input("Enter genre name (e.g., Action, Comedy): ").strip()
            await show_movies_by_genre(genre)
        elif choice == "5":
            title = input("Enter movie title: ").strip()
            await show_movie_details(title)
        elif choice == "6":
            title = input("Enter movie title: ").strip()
            filename = input("Output filename (default: movie_export.json): ").strip()
            filename = filename if filename else "movie_export.json"
            await export_to_json(title, filename)
        else:
            print("\n❌ Invalid choice. Please try again.")

        input("\nPress Enter to continue...")


async def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "stats":
            await show_stats()
        elif command == "search" and len(sys.argv) > 2:
            await search_movies(sys.argv[2])
        elif command == "top":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            await show_top_movies(limit)
        elif command == "genre" and len(sys.argv) > 2:
            await show_movies_by_genre(sys.argv[2])
        elif command == "details" and len(sys.argv) > 2:
            await show_movie_details(sys.argv[2])
        else:
            print("Usage:")
            print("  python explore_mongodb.py                  # Interactive mode")
            print("  python explore_mongodb.py stats            # Show statistics")
            print("  python explore_mongodb.py search <query>   # Search movies")
            print("  python explore_mongodb.py top [N]          # Show top N movies")
            print("  python explore_mongodb.py genre <name>     # Movies by genre")
            print("  python explore_mongodb.py details <title>  # Movie details")
    else:
        await interactive_menu()


if __name__ == "__main__":
    asyncio.run(main())
