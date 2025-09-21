"""
Configuration settings for SafeAir Navigator
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SafeAir Navigator"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Database
    DATABASE_URL: str = "postgresql://safeair:safeair@localhost/safeair_navigator"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # External APIs
    GOOGLE_MAPS_API_KEY: str = "AIzaSyDe9bOC_Se9pgpF3zYkXO4N3g-94ZQTmz8"
    GEMINI_API_KEY: str = "AIzaSyAFP7JHfQdcLgEpZ9vG115aXxKV1XfN1NI"
    OPENAQ_BASE_URL: str = "https://api.openaq.org/v2/"
    TRAFFIC_SIGNAL_API: str = "http://localhost:8001/mock-signals"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    class Config:
        env_file = ".env"


settings = Settings()