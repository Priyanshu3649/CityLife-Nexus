"""
Analytics API endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_analytics():
    """Get analytics data - placeholder"""
    return {"message": "Analytics endpoints - coming soon"}