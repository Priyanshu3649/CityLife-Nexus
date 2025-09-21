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
from app.services.transit_service import transit_service
from app.services.weather_service import weather_service
from app.services.traffic_light_service import traffic_light_service
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


@router.post("/optimize", response_model=List[RouteOption])
async def optimize_routes(
    origin: CoordinatesSchema,
    destination: CoordinatesSchema,
    route_type: str = Query("balanced", regex="^(fastest|cleanest|safest|balanced|eco_friendly)$"),
    departure_time: Optional[datetime] = None,
    current_session: Optional[UserSessionResponse] = Depends(get_optional_session)
):
    """Get optimized routes with intelligent scoring"""
    
    from app.services.route_optimizer import route_optimizer
    from app.schemas.user import UserPreferences, HealthProfile
    
    # Extract user preferences and health profile
    user_preferences = None
    health_profile = None
    
    if current_session:
        if current_session.preferences:
            try:
                user_preferences = UserPreferences(**current_session.preferences)
            except Exception:
                pass
        
        if current_session.health_profile:
            try:
                health_profile = HealthProfile(**current_session.health_profile)
            except Exception:
                pass
    
    # Use route optimizer for intelligent routing
    optimized_routes = await route_optimizer.optimize_route(
        origin=origin,
        destination=destination,
        user_preferences=user_preferences,
        health_profile=health_profile,
        departure_time=departure_time,
        route_type=route_type
    )
    
    if not optimized_routes:
        raise HTTPException(
            status_code=404,
            detail="No optimized routes found between the specified points"
        )
    
    return optimized_routes


@router.post("/route-comparison", response_model=RouteComparison)
async def compare_routes(
    origin: CoordinatesSchema,
    destination: CoordinatesSchema,
    departure_time: Optional[datetime] = None,
    current_session: Optional[UserSessionResponse] = Depends(get_optional_session)
):
    """Compare different route options with intelligent scoring"""
    
    from app.services.route_optimizer import route_optimizer
    from app.schemas.user import UserPreferences, HealthProfile
    
    # Extract user preferences and health profile
    user_preferences = None
    health_profile = None
    
    if current_session:
        if current_session.preferences:
            try:
                user_preferences = UserPreferences(**current_session.preferences)
            except Exception:
                pass
        
        if current_session.health_profile:
            try:
                health_profile = HealthProfile(**current_session.health_profile)
            except Exception:
                pass
    
    # Use route optimizer for intelligent comparison
    route_comparison = await route_optimizer.compare_routes(
        origin=origin,
        destination=destination,
        user_preferences=user_preferences,
        health_profile=health_profile,
        departure_time=departure_time
    )
    
    if not route_comparison:
        raise HTTPException(
            status_code=404,
            detail="No routes found between the specified points"
        )
    
    return route_comparison


@router.post("/route-metrics")
async def calculate_route_metrics(
    route: RouteOption,
    baseline_route: Optional[RouteOption] = None
):
    """Calculate efficiency metrics for a route"""
    
    from app.services.route_optimizer import route_optimizer
    
    metrics = await route_optimizer.calculate_route_efficiency_metrics(
        route=route,
        baseline_route=baseline_route
    )
    
    return metrics


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


@router.post("/transit/multimodal")
async def get_multimodal_routes(
    origin: CoordinatesSchema,
    destination: CoordinatesSchema,
    departure_time: Optional[datetime] = None,
    current_session: Optional[UserSessionResponse] = Depends(get_optional_session)
):
    """Get multimodal transit routes combining walking and public transport"""
    
    if departure_time is None:
        departure_time = datetime.now()
    
    routes = await transit_service.find_multimodal_routes(
        origin=origin,
        destination=destination,
        departure_time=departure_time
    )
    
    if not routes:
        raise HTTPException(
            status_code=404,
            detail="No transit routes found between the specified points. This might be outside supported cities or no suitable transit connections available."
        )
    
    return {
        "routes": routes,
        "supported_cities": transit_service.get_supported_cities(),
        "origin_city": transit_service.get_city_from_coordinates(origin),
        "destination_city": transit_service.get_city_from_coordinates(destination)
    }


@router.get("/transit/cities")
async def get_supported_cities():
    """Get list of cities with transit support"""
    
    cities = transit_service.get_supported_cities()
    city_details = {}
    
    for city_code in cities:
        city_info = transit_service.get_city_info(city_code)
        if city_info:
            city_details[city_code] = {
                "name": city_info["name"],
                "center": city_info["center"],
                "population": city_info.get("population"),
                "has_metro": city_info.get("has_metro", False),
                "has_brt": city_info.get("has_brt", False),
                "has_local_train": city_info.get("has_local_train", False),
                "metro_system": city_info.get("metro_system"),
                "bus_system": city_info.get("bus_system")
            }
    
    return {
        "supported_cities": city_details,
        "total_cities": len(cities)
    }


@router.get("/transit/city/{city_code}")
async def get_city_transit_info(city_code: str):
    """Get detailed transit information for a specific city"""
    
    city_info = transit_service.get_city_info(city_code)
    
    if not city_info:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city_code}' not found or not supported"
        )
    
    return city_info


@router.get("/transit/realtime/{route_id}")
async def get_transit_realtime_updates(route_id: str):
    """Get real-time updates for a specific transit route"""
    
    updates = await transit_service.get_real_time_updates(route_id)
    
    return updates


@router.get("/transit/accessibility/{stop_id}")
async def get_transit_accessibility(stop_id: str):
    """Get accessibility information for a transit stop"""
    
    accessibility_info = await transit_service.get_transit_accessibility_info(stop_id)
    
    return accessibility_info


@router.post("/transit/carbon-footprint")
async def calculate_transit_carbon_footprint(
    route_data: dict,
    passenger_count: int = Query(1, ge=1, le=10, description="Number of passengers")
):
    """Calculate carbon footprint for a transit route"""
    
    try:
        # Create a simplified route object from the provided data
        # In a real implementation, you'd have proper schema validation
        from app.services.transit_service import MultimodalRoute, TransitLeg
        
        # For now, return a simplified calculation
        distance_km = route_data.get("total_distance_km", 10)
        transport_types = route_data.get("transport_types", ["metro"])
        
        # Calculate emissions based on transport mix
        emission_factors = {
            "walking": 0.0,
            "metro": 0.04,
            "bus": 0.08,
            "train": 0.06,
            "car": 0.21
        }
        
        total_emissions = 0.0
        for transport_type in transport_types:
            factor = emission_factors.get(transport_type, 0.1)
            total_emissions += distance_km * factor * passenger_count
        
        car_emissions = distance_km * emission_factors["car"] * passenger_count
        savings = max(0, car_emissions - total_emissions)
        
        return {
            "total_emissions_kg": round(total_emissions, 3),
            "car_emissions_kg": round(car_emissions, 3),
            "savings_kg": round(savings, 3),
            "savings_percentage": round((savings / car_emissions * 100) if car_emissions > 0 else 0, 1),
            "passenger_count": passenger_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error calculating carbon footprint: {str(e)}"
        )


@router.get("/weather/route-impact")
async def get_weather_route_impact(
    origin: CoordinatesSchema,
    destination: CoordinatesSchema,
    departure_time: Optional[datetime] = None
):
    """Get weather impact analysis for a route"""
    
    if departure_time is None:
        departure_time = datetime.now()
    
    # Get weather data for origin and destination
    origin_weather = await weather_service.get_current_weather(origin)
    destination_weather = await weather_service.get_current_weather(destination)
    
    # Calculate basic route impact based on weather conditions
    route_impact = {
        "overall_impact": "low",
        "speed_factor": 1.0,
        "safety_factor": 1.0,
        "visibility_factor": 1.0,
        "recommendations": []
    }
    
    # Analyze weather conditions
    if origin_weather:
        condition = origin_weather.weather_condition.lower()
        if "rain" in condition or "storm" in condition:
            route_impact["overall_impact"] = "high"
            route_impact["speed_factor"] = 0.7
            route_impact["safety_factor"] = 0.6
            route_impact["recommendations"].append("Heavy rain detected. Consider delaying travel or using covered transport.")
        elif "fog" in condition or "mist" in condition:
            route_impact["overall_impact"] = "medium"
            route_impact["visibility_factor"] = 0.5
            route_impact["recommendations"].append("Poor visibility due to fog. Drive carefully and use headlights.")
    
    return {
        "origin_weather": origin_weather,
        "destination_weather": destination_weather,
        "route_impact": route_impact,
        "recommendations": route_impact.get("recommendations", [])
    }


@router.get("/location/autocomplete")
async def get_location_autocomplete(
    input_text: str = Query(..., description="Text input for location search"),
    bias_to_ncr: bool = Query(True, description="Bias results to Delhi NCR region"),
    types: Optional[str] = Query(None, description="Place types (comma-separated)")
):
    """Get location autocomplete suggestions with Delhi NCR bias"""
    
    if len(input_text.strip()) < 2:
        return {"predictions": []}
    
    place_types = types.split(",") if types else None
    
    suggestions = await maps_service.get_place_autocomplete(
        input_text=input_text,
        bias_to_ncr=bias_to_ncr,
        types=place_types
    )
    
    # Format suggestions for frontend
    formatted_suggestions = []
    for suggestion in suggestions:
        formatted_suggestions.append({
            "place_id": suggestion.get("place_id"),
            "description": suggestion.get("description"),
            "main_text": suggestion.get("structured_formatting", {}).get("main_text", ""),
            "secondary_text": suggestion.get("structured_formatting", {}).get("secondary_text", ""),
            "types": suggestion.get("types", [])
        })
    
    return {
        "predictions": formatted_suggestions,
        "input_text": input_text,
        "biased_to_ncr": bias_to_ncr
    }


@router.get("/location/details/{place_id}")
async def get_place_details(place_id: str):
    """Get detailed place information including coordinates"""
    
    place_details = await maps_service.get_place_details(place_id)
    
    if not place_details:
        raise HTTPException(
            status_code=404,
            detail=f"Place details not found for place_id: {place_id}"
        )
    
    # Extract coordinates
    geometry = place_details.get("geometry", {})
    location = geometry.get("location", {})
    
    return {
        "place_id": place_details.get("place_id"),
        "name": place_details.get("name"),
        "formatted_address": place_details.get("formatted_address"),
        "coordinates": {
            "latitude": location.get("lat"),
            "longitude": location.get("lng")
        },
        "types": place_details.get("types", []),
        "geometry": geometry
    }


@router.get("/traffic-lights/near")
async def get_nearby_traffic_lights(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_km: float = Query(2.0, description="Search radius in kilometers", ge=0.1, le=10.0)
):
    """Get traffic lights near a location in Delhi NCR"""
    
    coordinates = CoordinatesSchema(latitude=latitude, longitude=longitude)
    
    nearby_signals = await traffic_light_service.get_traffic_signals_near_location(
        coordinates=coordinates,
        radius_km=radius_km
    )
    
    # Format response
    signals_data = []
    for signal in nearby_signals:
        distance = traffic_light_service._calculate_distance(coordinates, signal.coordinates)
        
        signals_data.append({
            "signal_id": signal.light_id,
            "intersection_name": signal.intersection_name,
            "coordinates": {
                "latitude": signal.coordinates.latitude,
                "longitude": signal.coordinates.longitude
            },
            "distance_km": round(distance, 3),
            "current_state": {
                "color": signal.current_color.value,
                "time_remaining": signal.time_remaining,
                "cycle_duration": signal.cycle_duration
            },
            "road_type": signal.road_type.value,
            "features": {
                "is_smart_signal": signal.is_smart_signal,
                "has_countdown_timer": signal.has_countdown_timer,
                "pedestrian_crossing": signal.pedestrian_crossing
            },
            "last_updated": signal.last_updated.isoformat()
        })
    
    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "search_radius_km": radius_km,
        "signals_found": len(signals_data),
        "traffic_signals": signals_data
    }


@router.get("/traffic-lights/{signal_id}")
async def get_traffic_signal_details(signal_id: str):
    """Get detailed information about a specific traffic signal"""
    
    signal = await traffic_light_service.get_traffic_signal_by_id(signal_id)
    
    if not signal:
        raise HTTPException(
            status_code=404,
            detail=f"Traffic signal not found: {signal_id}"
        )
    
    return {
        "signal_id": signal.light_id,
        "intersection_name": signal.intersection_name,
        "coordinates": {
            "latitude": signal.coordinates.latitude,
            "longitude": signal.coordinates.longitude
        },
        "current_state": {
            "color": signal.current_color.value,
            "time_remaining": signal.time_remaining,
            "cycle_duration": signal.cycle_duration
        },
        "road_classification": {
            "type": signal.road_type.value,
            "description": {
                "major_arterial": "Major arterial road (NH, Ring Road)",
                "arterial": "Arterial road (Main city roads)",
                "collector": "Collector road (Sector/colony roads)",
                "local": "Local street"
            }.get(signal.road_type.value, "Unknown")
        },
        "features": {
            "is_smart_signal": signal.is_smart_signal,
            "has_countdown_timer": signal.has_countdown_timer,
            "pedestrian_crossing": signal.pedestrian_crossing
        },
        "timing_pattern": traffic_light_service.cycle_timings[signal.road_type],
        "delhi_ncr_context": {
            "peak_hours": traffic_light_service.peak_hours,
            "current_peak_status": traffic_light_service._is_peak_hour()
        },
        "last_updated": signal.last_updated.isoformat()
    }


@router.post("/geocode/enhanced")
async def enhanced_geocode(
    address: str = Query(..., description="Address to geocode"),
    bias_to_ncr: bool = Query(True, description="Bias results to Delhi NCR region")
):
    """Enhanced geocoding with Delhi NCR bias"""
    
    coordinates = await maps_service.geocode_address(address, bias_to_ncr=bias_to_ncr)
    
    if not coordinates:
        raise HTTPException(
            status_code=404,
            detail="Address not found or geocoding failed"
        )
    
    # Check if within Delhi NCR bounds
    within_ncr = maps_service._is_within_ncr_bounds(
        coordinates.latitude, coordinates.longitude
    )
    
    return {
        "address": address,
        "coordinates": coordinates,
        "location_context": {
            "within_delhi_ncr": within_ncr,
            "biased_search": bias_to_ncr,
            "region": "Delhi NCR" if within_ncr else "Outside Delhi NCR"
        }
    }