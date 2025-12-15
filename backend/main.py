from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from routes.job_routes import router as job_router
from routes.cv_routes import router as cv_router
from routes.search_routes import router as search_router
from routes.ats_routes import router as ats_router
from routes.assistant_routes import router as assistant_router
from routes.smart_assistant_routes import router as smart_assistant_router

# Create FastAPI app
app = FastAPI(
    title="Career-Match Backend API",
    description="A smart job matching engine for the Moroccan job market using TF-IDF and cosine similarity",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(job_router)
app.include_router(cv_router) 
app.include_router(search_router)
app.include_router(ats_router)
app.include_router(assistant_router)  # Basic Assistant
app.include_router(smart_assistant_router)  # Smart Assistant with LLM

@app.get("/")
async def root():
    return {
        "message": " Career-Match Backend API",
        "version": "1.0.0",
        "description": "Smart job matching engine for Moroccan job market",
        "endpoints": {
            "all_jobs": "GET /jobs/all",
            "search_jobs": "GET /jobs/search?query=your_query&top_k=5",
            "job_search_link": "GET /jobs/{job_title}/search-link",
            "categories": "GET /jobs/categories",
            "jobs_by_category": "GET /jobs/category/{category_name}",
            "health": "GET /jobs/health"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Career-Match Backend",
        "version": "1.0.0",
        "features": [
            "TF-IDF based job matching",
            "Cosine similarity scoring",
            "Moroccan job market focus",
            "Multiple job search platforms integration",
            "RESTful API with automatic documentation"
        ],
        "matching_algorithm": {
            "technique": "TF-IDF + Cosine Similarity",
            "weighted_features": {
                "job_title": 3,
                "required_skills": 2,
                "description": 1
            },
            "preprocessing": "lowercasing, punctuation removal, stop words removal"
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