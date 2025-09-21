"""
SafeAir Navigator - Simplified Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("SafeAir Navigator starting up...")
    yield
    # Shutdown
    print("SafeAir Navigator shutting down...")


app = FastAPI(
    title="SafeAir Navigator API",
    description="Smart navigation system with traffic signal coordination and pollution-aware routing",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "SafeAir Navigator API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "safeair-navigator"}


@app.get("/api/v1/test")
async def test_endpoint():
    return {"message": "API is working!", "status": "success"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )