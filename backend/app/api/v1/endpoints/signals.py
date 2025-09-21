"""
Traffic signals API endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_signals():
    """Get traffic signals - placeholder"""
    return {"message": "Traffic signals endpoints - coming soon"}