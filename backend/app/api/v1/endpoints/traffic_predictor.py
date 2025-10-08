"""
Traffic prediction API endpoints for congestion forecasting
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.traffic_predictor_service import traffic_predictor_service
from app.schemas.base import CoordinatesSchema
from app.schemas.traffic import TrafficPrediction
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.post("/predict-route-traffic", response_model=List[TrafficPrediction])
async def predict_route_traffic_density(
    route_coordinates: List[CoordinatesSchema],
    departure_time: Optional[datetime] = None,
    vehicle_speed_kmh: float = Query(30.0, ge=10, le=100, description="Average vehicle speed in km/h")
):
    """
    Predict traffic density for each segment of a route at estimated arrival times
    
    Args:
        route_coordinates: List of coordinates representing the route
        departure_time: When the journey starts (defaults to current time)
        vehicle_speed_kmh: Average vehicle speed in km/h
        
    Returns:
        List of traffic predictions for each segment
    """
    if len(route_coordinates) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 coordinates required for route analysis"
        )
    
    if departure_time is None:
        departure_time = datetime.utcnow()
    
    predictions = await traffic_predictor_service.predict_traffic_density(
        route_segments=route_coordinates,
        departure_time=departure_time,
        vehicle_speed_kmh=vehicle_speed_kmh
    )
    
    return predictions


@router.post("/route-traffic-summary")
async def get_route_traffic_prediction_summary(
    route_coordinates: List[CoordinatesSchema],
    departure_time: Optional[datetime] = None,
    vehicle_speed_kmh: float = Query(30.0, ge=10, le=100)
):
    """
    Get a summary of traffic predictions for the entire route
    
    Args:
        route_coordinates: List of coordinates representing the route
        departure_time: When the journey starts (defaults to current time)
        vehicle_speed_kmh: Average vehicle speed in km/h
        
    Returns:
        Summary of traffic predictions for the route
    """
    if len(route_coordinates) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 coordinates required for route analysis"
        )
    
    if departure_time is None:
        departure_time = datetime.utcnow()
    
    # Get detailed predictions
    predictions = await traffic_predictor_service.predict_traffic_density(
        route_segments=route_coordinates,
        departure_time=departure_time,
        vehicle_speed_kmh=vehicle_speed_kmh
    )
    
    # Generate summary
    summary = await traffic_predictor_service.get_traffic_prediction_summary(predictions)
    
    return summary


@router.post("/bulk-predict-routes")
async def bulk_predict_multiple_routes(
    routes_data: List[dict],
    departure_time: Optional[datetime] = None
):
    """
    Predict traffic for multiple routes at once
    
    Args:
        routes_data: List of route data dictionaries with coordinates
        departure_time: When the journey starts (defaults to current time)
        
    Returns:
        Predictions for all routes
    """
    if not routes_data:
        raise HTTPException(
            status_code=400,
            detail="At least one route required"
        )
    
    if len(routes_data) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 routes allowed per request"
        )
    
    if departure_time is None:
        departure_time = datetime.utcnow()
    
    results = []
    
    for route_data in routes_data:
        try:
            route_coordinates = [
                CoordinatesSchema(
                    latitude=coord["latitude"],
                    longitude=coord["longitude"]
                ) for coord in route_data.get("coordinates", [])
            ]
            
            if len(route_coordinates) < 2:
                results.append({
                    "route_id": route_data.get("route_id", "unknown"),
                    "predictions": [],
                    "status": "error",
                    "error": "At least 2 coordinates required"
                })
                continue
            
            predictions = await traffic_predictor_service.predict_traffic_density(
                route_segments=route_coordinates,
                departure_time=departure_time,
                vehicle_speed_kmh=route_data.get("vehicle_speed_kmh", 30.0)
            )
            
            results.append({
                "route_id": route_data.get("route_id", "unknown"),
                "predictions": predictions,
                "status": "success"
            })
            
        except Exception as e:
            results.append({
                "route_id": route_data.get("route_id", "unknown"),
                "predictions": [],
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_routes": len(routes_data),
        "successful_predictions": len([r for r in results if r["status"] == "success"]),
        "results": results
    }