"""
Test TMDB API connection and fetch sample data
"""
import asyncio
from services.tmdb_service import TMDBService


async def test_tmdb_api():
    """Test TMDB API connection"""
    print("\n" + "="*60)
    print("🎬 CineFeels - TMDB API Test")
    print("="*60 + "\n")

    service = TMDBService()

    try:
        # Test 1: Get genres
        print("📋 Test 1: Fetching movie genres...")
        genres_data = await service.get_genres()
        genres = genres_data.get("genres", [])
        print(f"   ✅ Found {len(genres)} genres")
        for genre in genres[:5]:
            print(f"      • {genre['name']} (ID: {genre['id']})")
        print()

        # Test 2: Get popular movies
        print("🔥 Test 2: Fetching popular movies (page 1)...")
        popular_data = await service.get_popular_movies(page=1)
        movies = popular_data.get("results", [])
        print(f"   ✅ Found {len(movies)} movies")
        for movie in movies[:3]:
            print(f"      • {movie['title']} ({movie.get('release_date', 'N/A')[:4]})")
            print(f"        Rating: {movie.get('vote_average')}/10 | Popularity: {movie.get('popularity')}")
        print()

        # Test 3: Get movie details
        if movies:
            movie_id = movies[0]["id"]
            print(f"🎥 Test 3: Fetching details for '{movies[0]['title']}'...")
            details = await service.get_movie_details(movie_id)
            print(f"   ✅ Title: {details['title']}")
            print(f"      Runtime: {details.get('runtime', 'N/A')} minutes")
            print(f"      Budget: ${details.get('budget', 0):,}")
            print(f"      Revenue: ${details.get('revenue', 0):,}")
            print(f"      Genres: {', '.join([g['name'] for g in details.get('genres', [])])}")

            # Show reviews count
            reviews = details.get("reviews", {}).get("results", [])
            print(f"      Reviews available: {len(reviews)}")
            print()

        # Test 4: Search movies
        print("🔍 Test 4: Searching for 'Inception'...")
        search_data = await service.search_movies("Inception")
        results = search_data.get("results", [])
        print(f"   ✅ Found {len(results)} results")
        for result in results[:3]:
            print(f"      • {result['title']} ({result.get('release_date', 'N/A')[:4]})")
        print()

        print("="*60)
        print("✨ All TMDB tests passed! API is working correctly! 🚀")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ TMDB API test failed: {e}")
        print("\n⚠️  Make sure you have set TMDB_API_KEY in your .env file")
        print("   Get your API key from: https://www.themoviedb.org/settings/api")
        print()


if __name__ == "__main__":
    asyncio.run(test_tmdb_api())
