"""
Eco-Score API endpoints for trip environmental impact
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.eco_score_service import eco_score_service, TripLog
from app.schemas.base import CoordinatesSchema
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.post("/calculate")
async def calculate_trip_eco_score(
    trip_id: str,
    trip_logs: List[dict],
    vehicle_type: str = Query("car", description="Type of vehicle used")
):
    """
    Calculate Eco-Score for a completed trip
    
    Args:
        trip_id: Unique identifier for the trip
        trip_logs: List of trip segment logs
        vehicle_type: Type of vehicle used
        
    Returns:
        Eco-Score metrics for the trip
    """
    if not trip_logs:
        raise HTTPException(
            status_code=400,
            detail="At least one trip log entry required"
        )
    
    # Convert trip logs to TripLog objects
    converted_logs = []
    for log_data in trip_logs:
        try:
            log = TripLog(
                segment_id=log_data["segment_id"],
                start_coords=CoordinatesSchema(
                    latitude=log_data["start_coords"]["latitude"],
                    longitude=log_data["start_coords"]["longitude"]
                ),
                end_coords=CoordinatesSchema(
                    latitude=log_data["end_coords"]["latitude"],
                    longitude=log_data["end_coords"]["longitude"]
                ),
                travel_time_seconds=log_data["travel_time_seconds"],
                aqi_exposure=log_data["aqi_exposure"],
                signals_crossed=log_data["signals_crossed"],
                signals_on_green=log_data["signals_on_green"],
                idling_time_seconds=log_data["idling_time_seconds"],
                distance_meters=log_data["distance_meters"]
            )
            converted_logs.append(log)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trip log format: {str(e)}"
            )
    
    eco_score_result = await eco_score_service.calculate_eco_score(
        trip_id=trip_id,
        trip_logs=converted_logs,
        vehicle_type=vehicle_type
    )
    
    return eco_score_result


@router.post("/compare-trips")
async def compare_multiple_trips(
    trip_ids: List[str]
):
    """
    Compare Eco-Scores for multiple trips
    
    Args:
        trip_ids: List of trip IDs to compare
        
    Returns:
        Comparison data for the trips
    """
    if not trip_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one trip ID required"
        )
    
    if len(trip_ids) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 trip IDs allowed per request"
        )
    
    comparison = await eco_score_service.get_trip_comparison(trip_ids)
    return comparison


@router.get("/user-statistics")
async def get_user_eco_statistics(
    user_id: Optional[str] = None
):
    """
    Get overall Eco-Score statistics for a user
    
    Args:
        user_id: Optional user ID (for multi-user support)
        
    Returns:
        User Eco-Score statistics
    """
    stats = await eco_score_service.get_user_eco_statistics(user_id)
    return stats


@router.post("/recommendations")
async def get_eco_score_recommendations(
    eco_score_data: dict
):
    """
    Get recommendations based on Eco-Score result
    
    Args:
        eco_score_data: Eco-Score calculation result
        
    Returns:
        List of recommendations
    """
    try:
        recommendations = await eco_score_service.get_eco_score_recommendations(eco_score_data)
        return {
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/trip/{trip_id}")
async def get_trip_eco_score(trip_id: str):
    """
    Get Eco-Score for a specific trip
    
    Args:
        trip_id: ID of the trip
        
    Returns:
        Eco-Score for the trip
    """
    if trip_id not in eco_score_service.trip_logs:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )
    
    return eco_score_service.trip_logs[trip_id]


@router.get("/all-trips")
async def get_all_trip_scores(
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of trips to return")
):
    """
    Get all trip scores (for admin/statistics purposes)
    
    Args:
        limit: Maximum number of trips to return
        
    Returns:
        List of all trip scores
    """
    all_trips = list(eco_score_service.trip_logs.values())
    return {
        "total_trips": len(all_trips),
        "trips": all_trips[:limit]
    }