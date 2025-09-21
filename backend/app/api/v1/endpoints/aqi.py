"""
Air quality API endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_aqi():
    """Get air quality data - placeholder"""
    return {"message": "AQI endpoints - coming soon"}