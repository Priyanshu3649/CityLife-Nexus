"""
CityLife Nexus - Simplified Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("CityLife Nexus starting up...")
    yield
    # Shutdown
    print("CityLife Nexus shutting down...")


app = FastAPI(
    title="CityLife Nexus API",
    description="Smart navigation system with traffic signal coordination and pollution-aware routing",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS using the same configuration as main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "CityLife Nexus API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "citylife-nexus"}


@app.get("/api/v1/test")
async def test_endpoint():
    return {"message": "API is working!", "status": "success"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )