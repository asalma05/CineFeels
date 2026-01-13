"""
CineFeels - FastAPI Application
Movie recommendation system based on emotional analysis
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import recommendations, movies, auth, mock_movies, mock_recommendations, user_data
from config.settings import get_settings

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="CineFeels API",
    description="Movie recommendation system based on emotional analysis using BERT",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(movies.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(user_data.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to CineFeels API",
        "description": "Movie recommendations based on emotional analysis",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "recommendations": "/api/v1/recommendations",
            "movies": "/api/v1/movies",
            "search": "/api/v1/movies/search/query",
            "genres": "/api/v1/movies/genres/list",
            "stats": "/api/v1/movies/stats/overview"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "CineFeels API"}


@app.get("/api/v1/info")
async def api_info():
    """API information"""
    return {
        "name": settings.app_name,
        "version": settings.api_version,
        "environment": settings.app_env,
        "model": settings.emotion_model,
        "emotions": {
            "base": settings.emotion_dimensions,
            "cinefeels": list(settings.cinefeels_emotions.keys())
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
