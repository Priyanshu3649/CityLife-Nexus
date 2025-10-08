"""
Google Maps API integration service with Delhi NCR focus
"""
import httpx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import asyncio
import logging

from app.core.config import settings
from app.schemas.base import CoordinatesSchema
from app.schemas.route import RouteOption, RouteSegment
from app.services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Service for Google Maps API integration with Delhi NCR focus"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Delhi NCR focus configuration
        self.delhi_ncr_bounds = settings.PRIMARY_REGION_BOUNDS
        self.extended_ncr_bounds = settings.EXTENDED_NCR_BOUNDS
        
        # Delhi NCR components for location bias
        self.delhi_ncr_components = [
            "country:IN",  # India only
            "administrative_area:Delhi",
            "administrative_area:Haryana", 
            "administrative_area:Uttar Pradesh"
        ]
    
    async def geocode_address(self, address: str, bias_to_ncr: bool = True) -> Optional[CoordinatesSchema]:
        """
        Convert address to coordinates using Google Geocoding API with Delhi NCR bias
        """
        # Check rate limit
        if not rate_limiter.is_allowed("google_maps"):
            logger.warning("Google Maps API rate limit exceeded for geocoding")
            return None
        
        url = f"{self.base_url}/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }
        
        # Bias results to Delhi NCR region
        if bias_to_ncr:
            # Add viewport bias to Delhi NCR
            bounds = self.extended_ncr_bounds
            viewport = f"{bounds['south']},{bounds['west']}|{bounds['north']},{bounds['east']}"
            params["bounds"] = viewport
            
            # Add component filtering for Indian locations
            params["components"] = "country:IN"
            
            # Add region bias
            params["region"] = "in"  # India
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                # Prioritize results within Delhi NCR
                for result in data["results"]:
                    location = result["geometry"]["location"]
                    lat, lng = location["lat"], location["lng"]
                    
                    # Check if within Delhi NCR bounds
                    if self._is_within_ncr_bounds(lat, lng):
                        return CoordinatesSchema(latitude=lat, longitude=lng)
                
                # If no result within NCR, return first result
                location = data["results"][0]["geometry"]["location"]
                return CoordinatesSchema(
                    latitude=location["lat"],
                    longitude=location["lng"]
                )
            elif data["status"] == "ZERO_RESULTS":
                logger.info(f"No results found for address: {address}")
                return None
            elif data["status"] == "OVER_QUERY_LIMIT":
                logger.error("Google Maps API quota exceeded")
                return None
            else:
                logger.error(f"Geocoding API error: {data['status']}")
                return None
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during geocoding: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None
    
    def _is_within_ncr_bounds(self, lat: float, lng: float) -> bool:
        """
        Check if coordinates are within Delhi NCR bounds
        """
        bounds = self.extended_ncr_bounds
        return (
            bounds["south"] <= lat <= bounds["north"] and
            bounds["west"] <= lng <= bounds["east"]
        )
    
    async def get_place_autocomplete(
        self, 
        input_text: str, 
        bias_to_ncr: bool = True,
        types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get place autocomplete suggestions with Delhi NCR bias
        """
        if not rate_limiter.is_allowed("google_maps"):
            logger.warning("Google Maps API rate limit exceeded for autocomplete")
            return []
        
        url = f"{self.base_url}/place/autocomplete/json"
        params = {
            "input": input_text,
            "key": self.api_key,
            "language": "en"
        }
        
        # Bias to Delhi NCR
        if bias_to_ncr:
            # Component restriction to India
            params["components"] = "country:in"
            
            # Set bounds for Delhi NCR region
            bounds = self.extended_ncr_bounds
            southwest = f"{bounds['south']},{bounds['west']}"
            northeast = f"{bounds['north']},{bounds['east']}"
            params["bounds"] = f"{southwest}|{northeast}"
            
            # Add location bias to central Delhi for better results
            params["location"] = "28.6139,77.2090"  # Connaught Place, Delhi
            params["radius"] = "50000"  # 50km radius
        
        # Add place types if specified
        if types:
            params["types"] = "|".join(types)
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK":
                return data["predictions"]
            elif data["status"] == "ZERO_RESULTS":
                return []
            else:
                logger.error(f"Autocomplete API error: {data['status']}")
                return []
                
        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return []
    
    async def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed place information including coordinates
        """
        url = f"{self.base_url}/place/details/json"
        params = {
            "place_id": place_id,
            "key": self.api_key,
            "fields": "name,formatted_address,geometry,place_id,types"
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK":
                return data["result"]
            else:
                logger.error(f"Place details API error: {data['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Place details error: {e}")
            return None
    
    async def reverse_geocode(self, coordinates: CoordinatesSchema) -> Optional[str]:
        """
        Convert coordinates to address using Google Reverse Geocoding API
        """
        url = f"{self.base_url}/geocode/json"
        params = {
            "latlng": f"{coordinates.latitude},{coordinates.longitude}",
            "key": self.api_key
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                return data["results"][0]["formatted_address"]
            
            return None
            
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None
    
    async def get_directions(
        self,
        origin: CoordinatesSchema,
        destination: CoordinatesSchema,
        waypoints: Optional[List[CoordinatesSchema]] = None,
        mode: str = "driving",
        avoid: Optional[List[str]] = None,
        departure_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get directions between two points using Google Directions API
        """
        # Check rate limit
        if not rate_limiter.is_allowed("google_maps"):
            logger.warning("Google Maps API rate limit exceeded for directions")
            return None
        
        url = f"{self.base_url}/directions/json"
        
        params = {
            "origin": f"{origin.latitude},{origin.longitude}",
            "destination": f"{destination.latitude},{destination.longitude}",
            "mode": mode,
            "key": self.api_key
        }
        
        # Add waypoints if provided
        if waypoints:
            waypoint_str = "|".join([
                f"{wp.latitude},{wp.longitude}" for wp in waypoints
            ])
            params["waypoints"] = waypoint_str
        
        # Add avoidances if provided
        if avoid:
            params["avoid"] = "|".join(avoid)
        
        # Add departure time for traffic-aware routing
        if departure_time:
            timestamp = int(departure_time.timestamp())
            params["departure_time"] = str(timestamp)
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK" and data["routes"]:
                return data
            elif data["status"] == "ZERO_RESULTS":
                logger.info("No route found between specified points")
                return None
            elif data["status"] == "OVER_QUERY_LIMIT":
                logger.error("Google Maps API quota exceeded")
                return None
            else:
                logger.error(f"Directions API error: {data['status']}")
                return None
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during directions request: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Directions error: {e}")
            return None
    
    async def calculate_distance_matrix(
        self,
        origins: List[CoordinatesSchema],
        destinations: List[CoordinatesSchema],
        mode: str = "driving",
        departure_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate distance matrix between multiple origins and destinations
        """
        url = f"{self.base_url}/distancematrix/json"
        
        origins_str = "|".join([
            f"{coord.latitude},{coord.longitude}" for coord in origins
        ])
        destinations_str = "|".join([
            f"{coord.latitude},{coord.longitude}" for coord in destinations
        ])
        
        params = {
            "origins": origins_str,
            "destinations": destinations_str,
            "mode": mode,
            "units": "metric",
            "key": self.api_key
        }
        
        if departure_time:
            timestamp = int(departure_time.timestamp())
            params["departure_time"] = str(timestamp)
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK":
                return data
            
            return None
            
        except Exception as e:
            print(f"Distance matrix error: {e}")
            return None
    
    def parse_route_from_directions(
        self, 
        directions_data: Dict[str, Any],
        route_type: str = "optimal"
    ) -> Optional[RouteOption]:
        """
        Parse Google Directions response into RouteOption schema
        """
        try:
            if not directions_data.get("routes"):
                return None
            
            route = directions_data["routes"][0]
            leg = route["legs"][0]
            
            # Extract basic route information
            distance_km = leg["distance"]["value"] / 1000  # Convert meters to km
            duration_minutes = leg["duration"]["value"] / 60  # Convert seconds to minutes
            
            # Extract start and end coordinates
            start_location = leg["start_location"]
            end_location = leg["end_location"]
            
            start_coords = CoordinatesSchema(
                latitude=start_location["lat"],
                longitude=start_location["lng"]
            )
            end_coords = CoordinatesSchema(
                latitude=end_location["lat"],
                longitude=end_location["lng"]
            )
            
            # Extract waypoints from route steps
            waypoints = []
            steps = leg.get("steps", [])
            
            for step in steps:
                step_start = step["start_location"]
                waypoints.append(CoordinatesSchema(
                    latitude=step_start["lat"],
                    longitude=step_start["lng"]
                ))
            
            # Add final destination
            waypoints.append(end_coords)
            
            # Create route segments for detailed analysis
            segments = []
            for i, step in enumerate(steps):
                step_start = step["start_location"]
                step_end = step["end_location"]
                
                segment = RouteSegment(
                    start_point=CoordinatesSchema(
                        latitude=step_start["lat"],
                        longitude=step_start["lng"]
                    ),
                    end_point=CoordinatesSchema(
                        latitude=step_end["lat"],
                        longitude=step_end["lng"]
                    ),
                    distance_meters=step["distance"]["value"],
                    aqi_level=0,  # Will be populated by AQI service
                    traffic_signals=[],  # Will be populated by traffic signal service
                    estimated_travel_time=step["duration"]["value"]
                )
                segments.append(segment)
            
            # Generate a UUID for the route (simplified for now)
            import uuid
            route_id = uuid.uuid4()
            
            return RouteOption(
                id=route_id,
                start_coords=start_coords,
                end_coords=end_coords,
                waypoints=waypoints,
                distance_km=round(distance_km, 2),
                estimated_time_minutes=int(duration_minutes),
                average_aqi=None,  # Will be calculated by AQI service
                route_score=None,  # Will be calculated by route optimization service
                route_type=route_type,
                segments=segments
            )
            
        except Exception as e:
            print(f"Route parsing error: {e}")
            return None
    
    async def get_multiple_route_options(
        self,
        origin: CoordinatesSchema,
        destination: CoordinatesSchema,
        departure_time: Optional[datetime] = None
    ) -> List[RouteOption]:
        """
        Get multiple route options with different preferences
        Only three route types: Fastest, Cleanest, and Safest
        """
        routes = []
        
        # Get fastest route (default - minimum travel time)
        fastest_directions = await self.get_directions(
            origin, destination, departure_time=departure_time
        )
        if fastest_directions:
            fastest_route = self.parse_route_from_directions(
                fastest_directions, "fastest"
            )
            if fastest_route:
                routes.append(fastest_route)
        
        # Get cleanest route (avoiding highways for potentially cleaner air)
        clean_directions = await self.get_directions(
            origin, destination, avoid=["highways"], departure_time=departure_time
        )
        if clean_directions:
            clean_route = self.parse_route_from_directions(
                clean_directions, "cleanest"
            )
            if clean_route:
                routes.append(clean_route)
        
        # Get safest route (default route marked as safest)
        # In a real implementation, this would use crime data, accident data, etc.
        safest_directions = await self.get_directions(
            origin, destination, departure_time=departure_time
        )
        if safest_directions:
            safest_route = self.parse_route_from_directions(
                safest_directions, "safest"
            )
            if safest_route:
                routes.append(safest_route)
        
        return routes
    
    async def get_traffic_conditions(
        self,
        coordinates: CoordinatesSchema,
        radius_km: float = 5.0
    ) -> Dict[str, Any]:
        """
        Get current traffic conditions around a location
        Note: This is a simplified implementation. 
        Real implementation would use Google Maps Roads API or Traffic API
        """
        # For demo purposes, return mock traffic data
        # In production, this would integrate with Google's traffic APIs
        
        return {
            "location": {
                "latitude": coordinates.latitude,
                "longitude": coordinates.longitude
            },
            "radius_km": radius_km,
            "traffic_level": "moderate",  # light, moderate, heavy
            "average_speed_kmh": 35,
            "incidents": [],
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def calculate_route_bounds(
        self, 
        waypoints: List[CoordinatesSchema]
    ) -> Dict[str, float]:
        """
        Calculate bounding box for a route
        """
        if not waypoints:
            return {}
        
        lats = [wp.latitude for wp in waypoints]
        lngs = [wp.longitude for wp in waypoints]
        
        return {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs)
        }
    
    def calculate_distance_between_points(
        self,
        point1: CoordinatesSchema,
        point2: CoordinatesSchema
    ) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [
            point1.latitude, point1.longitude,
            point2.latitude, point2.longitude
        ])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance
maps_service = GoogleMapsService()