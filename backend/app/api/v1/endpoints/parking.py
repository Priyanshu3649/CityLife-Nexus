"""
Smart parking API endpoints
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.parking_service import parking_service
from app.schemas.base import CoordinatesSchema
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.post("/find-nearby")
async def find_parking_near_destination(
    destination: CoordinatesSchema,
    radius_km: float = Query(2.0, ge=0.1, le=10.0, description="Search radius in kilometers"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of results to return")
):
    """
    Find parking spots near a destination
    
    Args:
        destination: Destination coordinates
        radius_km: Search radius in kilometers
        max_results: Maximum number of results to return
        
    Returns:
        List of parking spots sorted by availability and distance
    """
    parking_spots = await parking_service.find_parking_near_destination(
        destination=destination,
        radius_km=radius_km,
        max_results=max_results
    )
    
    return {
        "destination": destination,
        "radius_km": radius_km,
        "spots_found": len(parking_spots),
        "parking_spots": parking_spots
    }


@router.post("/predict-availability")
async def predict_parking_availability(
    destination: CoordinatesSchema,
    arrival_time: Optional[datetime] = None,
    duration_hours: float = Query(2.0, ge=0.5, le=24.0, description="Expected parking duration in hours")
):
    """
    Predict parking availability using ML clustering
    
    Args:
        destination: Destination coordinates
        arrival_time: Expected arrival time (defaults to current time)
        duration_hours: Expected parking duration in hours
        
    Returns:
        List of parking spots with predicted availability
    """
    if arrival_time is None:
        arrival_time = datetime.utcnow()
    
    predictions = await parking_service.predict_parking_availability(
        destination=destination,
        arrival_time=arrival_time,
        duration_hours=duration_hours
    )
    
    return {
        "destination": destination,
        "arrival_time": arrival_time,
        "duration_hours": duration_hours,
        "predictions": predictions,
        "spots_with_predictions": len(predictions)
    }


@router.get("/spot/{spot_id}")
async def get_parking_spot_details(spot_id: str):
    """
    Get detailed information about a specific parking spot
    
    Args:
        spot_id: ID of the parking spot
        
    Returns:
        Detailed parking spot information
    """
    if spot_id not in parking_service.parking_spots:
        raise HTTPException(
            status_code=404,
            detail=f"Parking spot {spot_id} not found"
        )
    
    spot = parking_service.parking_spots[spot_id]
    return spot.to_dict()


@router.put("/spot/{spot_id}/update")
async def update_parking_spot(
    spot_id: str,
    occupied: Optional[int] = None,
    capacity: Optional[int] = None
):
    """
    Update parking spot information
    
    Args:
        spot_id: ID of the parking spot
        occupied: Number of occupied spaces
        capacity: Total capacity
        
    Returns:
        Update status
    """
    success = await parking_service.update_parking_spot(
        spot_id=spot_id,
        occupied=occupied,
        capacity=capacity
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Parking spot {spot_id} not found"
        )
    
    return {
        "spot_id": spot_id,
        "updated": True,
        "message": "Parking spot updated successfully"
    }


@router.get("/statistics")
async def get_parking_statistics():
    """
    Get overall parking statistics
    
    Returns:
        Parking statistics
    """
    stats = await parking_service.get_parking_statistics()
    return stats


@router.post("/bulk-predict")
async def bulk_predict_parking_for_multiple_destinations(
    destinations_data: List[dict],
    arrival_time: Optional[datetime] = None
):
    """
    Predict parking availability for multiple destinations
    
    Args:
        destinations_data: List of destination data with coordinates
        arrival_time: Expected arrival time (defaults to current time)
        
    Returns:
        Predictions for all destinations
    """
    if not destinations_data:
        raise HTTPException(
            status_code=400,
            detail="At least one destination required"
        )
    
    if len(destinations_data) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 destinations allowed per request"
        )
    
    if arrival_time is None:
        arrival_time = datetime.utcnow()
    
    results = []
    
    for dest_data in destinations_data:
        try:
            destination = CoordinatesSchema(
                latitude=dest_data["latitude"],
                longitude=dest_data["longitude"]
            )
            
            duration_hours = dest_data.get("duration_hours", 2.0)
            
            predictions = await parking_service.predict_parking_availability(
                destination=destination,
                arrival_time=arrival_time,
                duration_hours=duration_hours
            )
            
            results.append({
                "destination": destination,
                "predictions": predictions,
                "status": "success"
            })
            
        except Exception as e:
            results.append({
                "destination": dest_data,
                "predictions": [],
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_destinations": len(destinations_data),
        "successful_predictions": len([r for r in results if r["status"] == "success"]),
        "results": results
    }