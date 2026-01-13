"""
TMDB API Service for fetching movie data
"""
import httpx
from typing import List, Dict, Optional
from config.settings import get_settings

settings = get_settings()


class TMDBService:
    """Service for interacting with The Movie Database API"""

    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self):
        self.api_key = settings.tmdb_api_key
        # Check if it's a Bearer token (JWT) or API key
        if self.api_key.startswith("eyJ"):
            # It's a JWT token, use Bearer authentication
            self.headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            self.use_bearer = True
        else:
            # It's an API key
            self.headers = {
                "accept": "application/json"
            }
            self.use_bearer = False

    async def get_popular_movies(self, page: int = 1) -> Dict:
        """
        Fetch popular movies from TMDB

        Args:
            page: Page number (default: 1)

        Returns:
            Dictionary containing movie results and metadata
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/movie/popular"
            params = {
                "language": "en-US",
                "page": page
            }

            # Add API key to params only if not using Bearer token
            if not self.use_bearer:
                params["api_key"] = self.api_key

            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_movie_details(self, movie_id: int) -> Dict:
        """
        Fetch detailed information for a specific movie

        Args:
            movie_id: TMDB movie ID

        Returns:
            Dictionary containing movie details
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/movie/{movie_id}"
            params = {
                "language": "en-US",
                "append_to_response": "credits,keywords,reviews"
            }

            if not self.use_bearer:
                params["api_key"] = self.api_key

            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_movie_reviews(self, movie_id: int, page: int = 1) -> Dict:
        """
        Fetch reviews for a specific movie

        Args:
            movie_id: TMDB movie ID
            page: Page number (default: 1)

        Returns:
            Dictionary containing review results
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/movie/{movie_id}/reviews"
            params = {
                "language": "en-US",
                "page": page
            }

            if not self.use_bearer:
                params["api_key"] = self.api_key

            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def discover_movies(
        self,
        with_genres: Optional[str] = None,
        sort_by: str = "popularity.desc",
        page: int = 1,
        year: Optional[int] = None
    ) -> Dict:
        """
        Discover movies with filters

        Args:
            with_genres: Comma-separated genre IDs
            sort_by: Sort criteria (default: popularity.desc)
            page: Page number (default: 1)
            year: Filter by release year

        Returns:
            Dictionary containing discovered movies
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/discover/movie"
            params = {
                "language": "en-US",
                "sort_by": sort_by,
                "page": page,
                "include_adult": False,
                "include_video": False
            }

            if not self.use_bearer:
                params["api_key"] = self.api_key

            if with_genres:
                params["with_genres"] = with_genres
            if year:
                params["year"] = year

            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_genres(self) -> Dict:
        """
        Fetch list of official TMDB movie genres

        Returns:
            Dictionary containing genre list
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/genre/movie/list"
            params = {
                "language": "en-US"
            }

            if not self.use_bearer:
                params["api_key"] = self.api_key

            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def search_movies(self, query: str, page: int = 1) -> Dict:
        """
        Search for movies by title

        Args:
            query: Search query
            page: Page number (default: 1)

        Returns:
            Dictionary containing search results
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/search/movie"
            params = {
                "language": "en-US",
                "query": query,
                "page": page,
                "include_adult": False
            }

            if not self.use_bearer:
                params["api_key"] = self.api_key

            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()


async def fetch_movies_batch(num_pages: int = 5) -> List[Dict]:
    """
    Fetch multiple pages of popular movies

    Args:
        num_pages: Number of pages to fetch (default: 5)

    Returns:
        List of all movies from all pages
    """
    service = TMDBService()
    all_movies = []

    for page in range(1, num_pages + 1):
        print(f"📥 Fetching page {page}/{num_pages}...")
        data = await service.get_popular_movies(page=page)
        all_movies.extend(data.get("results", []))

    print(f"✅ Fetched {len(all_movies)} movies total")
    return all_movies
