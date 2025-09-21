"""
Emergency alerts API endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_emergency():
    """Get emergency alerts - placeholder"""
    return {"message": "Emergency endpoints - coming soon"}