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
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
    
    # Database
    DATABASE_URL: str = "postgresql://safeair:safeair@localhost/safeair_navigator"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # External APIs
    GOOGLE_MAPS_API_KEY: str = "AIzaSyCq1RuMsaiWH1GV_Fo7avhlrmj1N8OfGIM"
    GEMINI_API_KEY: str = "AIzaSyAFP7JHfQdcLgEpZ9vG115aXxKV1XfN1NI"
    OPENAQ_BASE_URL: str = "https://api.openaq.org/v3/"
    OPENAQ_API_KEY: str = ""  # Add your OpenAQ API key here
    OPENWEATHER_API_KEY: str = ""  # Add your OpenWeatherMap API key here
    TRAFFIC_SIGNAL_API: str = "http://localhost:8001/mock-signals"
    
    # Delhi NCR Focus Configuration
    PRIMARY_REGION_BOUNDS: dict = {
        "north": 28.8406,  # North Delhi boundary
        "south": 28.4089,  # South Delhi boundary  
        "east": 77.3465,   # East Delhi boundary
        "west": 76.8420    # West Delhi boundary (includes Gurgaon)
    }
    EXTENDED_NCR_BOUNDS: dict = {
        "north": 28.9500,  # Extended to include Ghaziabad
        "south": 28.2500,  # Extended to include Faridabad
        "east": 77.5000,   # Extended to include Noida/Ghaziabad
        "west": 76.6000    # Extended to include Gurgaon
    }
    
    # Security
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    class Config:
        env_file = ".env"


settings = Settings()