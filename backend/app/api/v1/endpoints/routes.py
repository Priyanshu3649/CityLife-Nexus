"""
Route optimization API endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_routes():
    """Get available routes - placeholder"""
    return {"message": "Route endpoints - coming soon"}