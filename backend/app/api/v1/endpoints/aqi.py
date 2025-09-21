"""
Air quality API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.aqi_service import aqi_service
from app.schemas.base import CoordinatesSchema
from app.schemas.air_quality import (
    AQIReading, 
    RouteAQIData, 
    HealthImpactEstimate,
    AQIRequest
)
from app.schemas.user import UserSessionResponse, HealthProfile

router = APIRouter()


@router.post("/measurements", response_model=List[AQIReading])
async def get_aqi_measurements(
    coordinates: CoordinatesSchema,
    radius_km: float = Query(10.0, ge=0.1, le=50.0, description="Search radius in kilometers"),
    parameter: str = Query("pm25", description="Pollutant parameter (pm25, pm10, no2, o3)"),
    db: Session = Depends(get_db)
):
    """Get air quality measurements near a location"""
    
    readings = await aqi_service.get_measurements_by_location(
        coordinates=coordinates,
        radius_km=radius_km,
        parameter=parameter
    )
    
    # Store readings in database for historical analysis
    for reading in readings:
        await aqi_service.store_aqi_reading(db, reading)
    
    return readings


@router.post("/route-analysis", response_model=RouteAQIData)
async def analyze_route_aqi(
    route_coordinates: List[CoordinatesSchema],
    radius_km: float = Query(2.0, ge=0.1, le=10.0, description="Search radius around route points")
):
    """Analyze air quality along a route"""
    
    if len(route_coordinates) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 coordinates required for route analysis"
        )
    
    if len(route_coordinates) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 coordinates allowed for route analysis"
        )
    
    route_aqi_data = await aqi_service.get_route_aqi_data(
        route_coordinates=route_coordinates,
        radius_km=radius_km
    )
    
    return route_aqi_data


@router.post("/health-impact", response_model=HealthImpactEstimate)
async def calculate_health_impact(
    route_coordinates: List[CoordinatesSchema],
    travel_time_minutes: int = Query(..., ge=1, le=480, description="Estimated travel time in minutes"),
    current_session: Optional[UserSessionResponse] = Depends(get_optional_session)
):
    """Calculate health impact estimate for a route"""
    
    # Get AQI data for the route
    route_aqi_data = await aqi_service.get_route_aqi_data(route_coordinates)
    
    # Get user health profile if available
    health_profile = None
    if current_session and current_session.health_profile:
        try:
            health_profile = HealthProfile(**current_session.health_profile)
        except Exception:
            # Use default profile if parsing fails
            health_profile = None
    
    # Calculate health impact
    health_impact = aqi_service.calculate_health_impact(
        route_aqi_data=route_aqi_data,
        health_profile=health_profile,
        travel_time_minutes=travel_time_minutes
    )
    
    return health_impact


@router.get("/category")
def get_aqi_category(
    aqi_value: int = Query(..., ge=0, le=500, description="AQI value")
):
    """Get AQI category and color for a given AQI value"""
    
    category, color = aqi_service.get_aqi_category(aqi_value)
    
    return {
        "aqi_value": aqi_value,
        "category": category,
        "color": color,
        "health_message": _get_health_message(aqi_value)
    }


@router.post("/compare-routes")
async def compare_route_air_quality(
    route1_coordinates: List[CoordinatesSchema],
    route2_coordinates: List[CoordinatesSchema],
    travel_time1_minutes: int = Query(..., ge=1, le=480),
    travel_time2_minutes: int = Query(..., ge=1, le=480),
    current_session: Optional[UserSessionResponse] = Depends(get_optional_session)
):
    """Compare air quality between two routes"""
    
    # Analyze both routes
    route1_aqi = await aqi_service.get_route_aqi_data(route1_coordinates)
    route2_aqi = await aqi_service.get_route_aqi_data(route2_coordinates)
    
    # Get health profile
    health_profile = None
    if current_session and current_session.health_profile:
        try:
            health_profile = HealthProfile(**current_session.health_profile)
        except Exception:
            pass
    
    # Calculate health impacts
    impact1 = aqi_service.calculate_health_impact(
        route1_aqi, health_profile, travel_time1_minutes
    )
    impact2 = aqi_service.calculate_health_impact(
        route2_aqi, health_profile, travel_time2_minutes
    )
    
    # Determine recommendation
    if route1_aqi.average_aqi < route2_aqi.average_aqi:
        recommendation = "route1"
        reason = f"Route 1 has better air quality (AQI {route1_aqi.average_aqi} vs {route2_aqi.average_aqi})"
    elif route2_aqi.average_aqi < route1_aqi.average_aqi:
        recommendation = "route2"
        reason = f"Route 2 has better air quality (AQI {route2_aqi.average_aqi} vs {route1_aqi.average_aqi})"
    else:
        recommendation = "similar"
        reason = "Both routes have similar air quality"
    
    return {
        "route1": {
            "aqi_data": route1_aqi,
            "health_impact": impact1
        },
        "route2": {
            "aqi_data": route2_aqi,
            "health_impact": impact2
        },
        "recommendation": recommendation,
        "reason": reason,
        "pollution_exposure_difference": abs(
            impact1.estimated_exposure_pm25 - impact2.estimated_exposure_pm25
        )
    }


@router.get("/current-conditions")
async def get_current_air_quality(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    db: Session = Depends(get_db)
):
    """Get current air quality conditions at a specific location"""
    
    coordinates = CoordinatesSchema(latitude=latitude, longitude=longitude)
    
    readings = await aqi_service.get_measurements_by_location(
        coordinates=coordinates,
        radius_km=5.0
    )
    
    if not readings:
        raise HTTPException(
            status_code=404,
            detail="No air quality data available for this location"
        )
    
    # Get the most recent reading
    latest_reading = max(readings, key=lambda r: r.reading_time)
    
    # Store in database
    await aqi_service.store_aqi_reading(db, latest_reading)
    
    # Get category and health information
    category, color = aqi_service.get_aqi_category(latest_reading.aqi_value)
    
    return {
        "location": coordinates,
        "current_aqi": latest_reading.aqi_value,
        "category": category,
        "color": color,
        "pollutants": {
            "pm25": latest_reading.pm25,
            "pm10": latest_reading.pm10,
            "no2": latest_reading.no2,
            "o3": latest_reading.o3
        },
        "source": latest_reading.source,
        "last_updated": latest_reading.reading_time,
        "health_message": _get_health_message(latest_reading.aqi_value)
    }


def _get_health_message(aqi_value: int) -> str:
    """Get health message based on AQI value"""
    if aqi_value <= 50:
        return "Air quality is good. Ideal for outdoor activities."
    elif aqi_value <= 100:
        return "Air quality is acceptable for most people."
    elif aqi_value <= 150:
        return "Sensitive individuals should consider limiting outdoor activities."
    elif aqi_value <= 200:
        return "Everyone should limit outdoor activities."
    elif aqi_value <= 300:
        return "Health alert: everyone should avoid outdoor activities."
    else:
        return "Health emergency: everyone should stay indoors."