"""
Route optimization API endpoints
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.maps_service import maps_service
from app.schemas.base import CoordinatesSchema
from app.schemas.route import RouteOption, RouteRequest, RouteComparison
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.post("/geocode")
async def geocode_address(address: str = Query(..., description="Address to geocode")):
    """Convert address to coordinates"""
    coordinates = await maps_service.geocode_address(address)
    
    if not coordinates:
        raise HTTPException(
            status_code=404,
            detail="Address not found or geocoding failed"
        )
    
    return {
        "address": address,
        "coordinates": coordinates
    }


@router.post("/reverse-geocode")
async def reverse_geocode(coordinates: CoordinatesSchema):
    """Convert coordinates to address"""
    address = await maps_service.reverse_geocode(coordinates)
    
    if not address:
        raise HTTPException(
            status_code=404,
            detail="Address not found for coordinates"
        )
    
    return {
        "coordinates": coordinates,
        "address": address
    }


@router.post("/directions", response_model=List[RouteOption])
async def get_directions(
    origin: CoordinatesSchema,
    destination: CoordinatesSchema,
    waypoints: Optional[List[CoordinatesSchema]] = None,
    departure_time: Optional[datetime] = None,
    avoid: Optional[List[str]] = Query(None, description="Things to avoid: highways, tolls, ferries"),
    current_session: Optional[UserSessionResponse] = Depends(get_optional_session)
):
    """Get directions between two points"""
    
    # Get single route with specified parameters
    directions_data = await maps_service.get_directions(
        origin=origin,
        destination=destination,
        waypoints=waypoints,
        avoid=avoid,
        departure_time=departure_time
    )
    
    if not directions_data:
        raise HTTPException(
            status_code=404,
            detail="No route found between the specified points"
        )
    
    # Parse the route
    route = maps_service.parse_route_from_directions(directions_data)
    
    if not route:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse route data"
        )
    
    return [route]


@router.post("/route-options", response_model=List[RouteOption])
async def get_route_options(
    origin: CoordinatesSchema,
    destination: CoordinatesSchema,
    departure_time: Optional[datetime] = None,
    current_session: Optional[UserSessionResponse] = Depends(get_optional_session)
):
    """Get multiple route options (fast, clean, toll-free)"""
    
    routes = await maps_service.get_multiple_route_options(
        origin=origin,
        destination=destination,
        departure_time=departure_time
    )
    
    if not routes:
        raise HTTPException(
            status_code=404,
            detail="No routes found between the specified points"
        )
    
    return routes


@router.post("/route-comparison", response_model=RouteComparison)
async def compare_routes(
    origin: CoordinatesSchema,
    destination: CoordinatesSchema,
    departure_time: Optional[datetime] = None,
    current_session: Optional[UserSessionResponse] = Depends(get_optional_session)
):
    """Compare different route options"""
    
    routes = await maps_service.get_multiple_route_options(
        origin=origin,
        destination=destination,
        departure_time=departure_time
    )
    
    if not routes:
        raise HTTPException(
            status_code=404,
            detail="No routes found for comparison"
        )
    
    # Separate routes by type
    fast_route = None
    clean_route = None
    balanced_route = None
    
    for route in routes:
        if route.route_type == "fast":
            fast_route = route
        elif route.route_type == "clean":
            clean_route = route
        elif route.route_type == "optimal":
            balanced_route = route
    
    # Use first route as fallback if specific types not found
    if not fast_route:
        fast_route = routes[0]
    if not clean_route:
        clean_route = routes[-1] if len(routes) > 1 else routes[0]
    
    # Determine recommendation based on user preferences
    recommendation = "balanced"
    if current_session and current_session.preferences:
        time_priority = current_session.preferences.get("prioritize_time", 0.4)
        aqi_priority = current_session.preferences.get("prioritize_air_quality", 0.4)
        
        if time_priority > 0.6:
            recommendation = "fast"
        elif aqi_priority > 0.6:
            recommendation = "clean"
    
    return RouteComparison(
        fast_route=fast_route,
        clean_route=clean_route,
        balanced_route=balanced_route,
        recommendation=recommendation
    )


@router.post("/distance-matrix")
async def calculate_distance_matrix(
    origins: List[CoordinatesSchema],
    destinations: List[CoordinatesSchema],
    departure_time: Optional[datetime] = None
):
    """Calculate distance matrix between multiple points"""
    
    if len(origins) > 10 or len(destinations) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 origins and 10 destinations allowed"
        )
    
    matrix_data = await maps_service.calculate_distance_matrix(
        origins=origins,
        destinations=destinations,
        departure_time=departure_time
    )
    
    if not matrix_data:
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate distance matrix"
        )
    
    return matrix_data


@router.get("/traffic-conditions")
async def get_traffic_conditions(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_km: float = Query(5.0, description="Radius in kilometers", ge=0.1, le=50.0)
):
    """Get current traffic conditions around a location"""
    
    coordinates = CoordinatesSchema(latitude=latitude, longitude=longitude)
    
    traffic_data = await maps_service.get_traffic_conditions(
        coordinates=coordinates,
        radius_km=radius_km
    )
    
    return traffic_data


@router.post("/route-bounds")
def calculate_route_bounds(waypoints: List[CoordinatesSchema]):
    """Calculate bounding box for a route"""
    
    if not waypoints:
        raise HTTPException(
            status_code=400,
            detail="At least one waypoint is required"
        )
    
    bounds = maps_service.calculate_route_bounds(waypoints)
    
    return {
        "waypoints_count": len(waypoints),
        "bounds": bounds
    }


@router.post("/distance")
def calculate_distance(
    point1: CoordinatesSchema,
    point2: CoordinatesSchema
):
    """Calculate distance between two points"""
    
    distance_km = maps_service.calculate_distance_between_points(point1, point2)
    
    return {
        "point1": point1,
        "point2": point2,
        "distance_km": round(distance_km, 3),
        "distance_meters": round(distance_km * 1000, 1)
    }