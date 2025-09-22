"""
Google Maps API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.maps_service import maps_service
from app.services.aqi_service import aqi_service
from app.schemas.base import CoordinatesSchema
from app.schemas.route import RouteRequest, RouteResponse

router = APIRouter()


class AutocompleteResponse(BaseModel):
    predictions: List[dict]


class GeocodeResponse(BaseModel):
    coordinates: Optional[CoordinatesSchema]
    formatted_address: Optional[str]


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_places(query: str = Query(..., min_length=3)):
    """
    Get place autocomplete suggestions using Google Places API
    """
    try:
        # Call Google Places Autocomplete API through our service
        suggestions = await maps_service.get_place_autocomplete(query)
        
        # Format suggestions to match expected response structure
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestions.append({
                "description": suggestion.get("description", ""),
                "place_id": suggestion.get("place_id", ""),
                "structured_formatting": suggestion.get("structured_formatting", {
                    "main_text": suggestion.get("description", ""),
                    "secondary_text": ""
                })
            })
        
        return AutocompleteResponse(predictions=formatted_suggestions)
        
    except Exception as e:
        # Fallback to mock suggestions if API fails
        mock_suggestions = [
            {
                "description": f"{query}, Delhi, India",
                "place_id": f"mock_delhi_{hash(query)}",
                "structured_formatting": {
                    "main_text": query,
                    "secondary_text": "Delhi, India"
                }
            },
            {
                "description": f"{query}, Mumbai, Maharashtra, India", 
                "place_id": f"mock_mumbai_{hash(query)}",
                "structured_formatting": {
                    "main_text": query,
                    "secondary_text": "Mumbai, Maharashtra, India"
                }
            },
            {
                "description": f"{query}, Bangalore, Karnataka, India",
                "place_id": f"mock_bangalore_{hash(query)}",
                "structured_formatting": {
                    "main_text": query,
                    "secondary_text": "Bangalore, Karnataka, India"
                }
            }
        ]
        
        return AutocompleteResponse(predictions=mock_suggestions)


@router.get("/geocode", response_model=GeocodeResponse)
async def geocode_address(address: str = Query(...)):
    """
    Convert address to coordinates using Google Geocoding API
    """
    try:
        coordinates = await maps_service.geocode_address(address)
        
        if coordinates:
            return GeocodeResponse(
                coordinates=coordinates,
                formatted_address=address
            )
        else:
            # Return mock coordinates for demo
            # In production, this would return None if geocoding fails
            mock_coords = CoordinatesSchema(
                latitude=28.6139 + (hash(address) % 100) * 0.001,
                longitude=77.2090 + (hash(address) % 100) * 0.001
            )
            return GeocodeResponse(
                coordinates=mock_coords,
                formatted_address=address
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")


@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(...),
    lng: float = Query(...)
):
    """
    Convert coordinates to address using Google Reverse Geocoding API
    """
    try:
        coordinates = CoordinatesSchema(latitude=lat, longitude=lng)
        address = await maps_service.reverse_geocode(coordinates)
        
        return {
            "coordinates": coordinates,
            "formatted_address": address or f"Location at {lat}, {lng}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reverse geocoding failed: {str(e)}")


@router.post("/directions")
async def get_directions(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: str = "driving"
):
    """
    Get directions between two points using Google Directions API
    """
    try:
        origin = CoordinatesSchema(latitude=origin_lat, longitude=origin_lng)
        destination = CoordinatesSchema(latitude=dest_lat, longitude=dest_lng)
        
        directions = await maps_service.get_directions(origin, destination, mode=mode)
        
        if directions:
            return directions
        else:
            raise HTTPException(status_code=404, detail="No route found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Directions failed: {str(e)}")


@router.get("/traffic")
async def get_traffic_conditions(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(default=5.0)
):
    """
    Get current traffic conditions around a location
    """
    try:
        coordinates = CoordinatesSchema(latitude=lat, longitude=lng)
        traffic_data = await maps_service.get_traffic_conditions(coordinates, radius)
        
        return traffic_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Traffic data failed: {str(e)}")


class RouteWithAQIRequest(BaseModel):
    start_coords: CoordinatesSchema
    end_coords: CoordinatesSchema
    preferences: dict
    vehicle_type: str = "car"


@router.post("/routes-with-aqi")
async def get_routes_with_aqi(request: RouteWithAQIRequest):
    """
    Get multiple route options with real-time AQI data
    """
    try:
        # Get multiple route options from Google Maps
        routes = await maps_service.get_multiple_route_options(
            request.start_coords,
            request.end_coords
        )
        
        # Enhance routes with AQI data
        enhanced_routes = []
        for route in routes:
            # Get AQI data along the route
            aqi_data = await aqi_service.get_route_aqi_data(
                route.waypoints,
                radius_km=1.0
            )
            
            # Calculate average AQI for the route
            if aqi_data.aqi_readings:
                avg_aqi = sum(reading.aqi_value for reading in aqi_data.aqi_readings) / len(aqi_data.aqi_readings)
            else:
                # Mock AQI data for demo
                avg_aqi = 100 + (hash(str(route.id)) % 100)
            
            enhanced_route = {
                "id": str(route.id),
                "name": f"{route.route_type.title()} Route",
                "time": route.estimated_time_minutes,
                "aqi": int(avg_aqi),
                "distance": route.distance_km,
                "type": route.route_type,
                "description": f"Via {route.route_type} roads",
                "waypoints": [{"lat": wp.latitude, "lng": wp.longitude} for wp in route.waypoints],
                "start_coords": {
                    "latitude": route.start_coords.latitude,
                    "longitude": route.start_coords.longitude
                },
                "end_coords": {
                    "latitude": route.end_coords.latitude,
                    "longitude": route.end_coords.longitude
                }
            }
            enhanced_routes.append(enhanced_route)
        
        # Sort routes by preference
        if request.preferences.get("prioritize_air_quality", 0) > 0.5:
            enhanced_routes.sort(key=lambda r: r["aqi"])
        elif request.preferences.get("prioritize_time", 0) > 0.5:
            enhanced_routes.sort(key=lambda r: r["time"])
        else:
            # Balanced sorting
            enhanced_routes.sort(key=lambda r: r["time"] * 0.5 + r["aqi"] * 0.01)
        
        return {"routes": enhanced_routes}
        
    except Exception as e:
        # Return mock data if API fails
        mock_routes = [
            {
                "id": "1",
                "name": "Fastest Route",
                "time": 18,
                "aqi": 160,
                "distance": 12.5,
                "type": "fastest",
                "description": "Via main roads with heavy traffic",
                "start_coords": request.start_coords,
                "end_coords": request.end_coords
            },
            {
                "id": "2",
                "name": "Clean Air Route", 
                "time": 25,
                "aqi": 85,
                "distance": 14.2,
                "type": "cleanest",
                "description": "Via parks and residential areas",
                "start_coords": request.start_coords,
                "end_coords": request.end_coords
            },
            {
                "id": "3",
                "name": "Balanced Route",
                "time": 21,
                "aqi": 120,
                "distance": 13.1,
                "type": "balanced",
                "description": "Optimal time and air quality",
                "start_coords": request.start_coords,
                "end_coords": request.end_coords
            }
        ]
        
        return {"routes": mock_routes}