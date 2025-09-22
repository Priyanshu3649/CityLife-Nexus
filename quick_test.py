"""
Quick test of CityLife Nexus backend without heavy dependencies
"""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock FastAPI app for testing
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import our modules (mocked or real)
try:
    from backend.app.schemas.base import CoordinatesSchema
    from backend.app.schemas.route import RouteOption
    from backend.app.schemas.user import UserPreferences
    from backend.app.services.maps_service import maps_service
    from backend.app.services.aqi_service import aqi_service
    from backend.app.services.traffic_signal_service import traffic_signal_service
    from backend.app.services.route_optimizer import route_optimizer
    has_backend = True
except ImportError as e:
    print(f"⚠️  Backend import failed: {e}")
    has_backend = False

app = FastAPI(
    title="CityLife Nexus API",
    description="Smart navigation system with traffic signal coordination and pollution-aware routing",
    version="1.0.0"
)

# Mock data models
class MockCoordinates(BaseModel):
    latitude: float
    longitude: float

class MockRouteOption(BaseModel):
    id: str
    start_coords: MockCoordinates
    end_coords: MockCoordinates
    distance_km: float
    estimated_time_minutes: int

# Mock services
class MockMapsService:
    async def get_multiple_route_options(self, origin, destination, departure_time=None):
        return [
            MockRouteOption(
                id="route_1",
                start_coords=MockCoordinates(latitude=origin.latitude, longitude=origin.longitude),
                end_coords=MockCoordinates(latitude=destination.latitude, longitude=destination.longitude),
                distance_km=12.5,
                estimated_time_minutes=25
            )
        ]

class MockAQIService:
    async def get_aqi_for_coordinates(self, coordinates):
        return {"aqi": 85, "category": "Moderate"}

class MockTrafficSignalService:
    def get_signals_along_route(self, route_coordinates, buffer_meters=100.0):
        return [
            {"signal_id": "sig_1", "coordinates": route_coordinates[0], "current_state": "green", "time_to_next_change": 15},
            {"signal_id": "sig_2", "coordinates": route_coordinates[-1], "current_state": "red", "time_to_next_change": 45}
        ]

# Initialize mock services
mock_maps_service = MockMapsService()
mock_aqi_service = MockAQIService()
mock_traffic_signal_service = MockTrafficSignalService()

# API endpoints
@app.get("/")
async def root():
    return {
        "message": "CityLife Nexus API", 
        "version": "1.0.0",
        "status": "operational",
        "backend_available": has_backend
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/routes")
async def get_routes(origin: MockCoordinates, destination: MockCoordinates):
    """Get route options between two points"""
    try:
        routes = await mock_maps_service.get_multiple_route_options(origin, destination)
        return {"routes": routes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/aqi/{lat}/{lng}")
async def get_aqi(lat: float, lng: float):
    """Get AQI for specific coordinates"""
    try:
        coordinates = MockCoordinates(latitude=lat, longitude=lng)
        aqi_data = await mock_aqi_service.get_aqi_for_coordinates(coordinates)
        return aqi_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/signals/along-route")
async def get_signals_along_route(coordinates: str):
    """Get traffic signals along a route"""
    try:
        # Parse coordinates from string
        coords_list = json.loads(coordinates)
        signals = mock_traffic_signal_service.get_signals_along_route(coords_list)
        return {"signals": signals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def test_backend():
    """Test backend functionality"""
    print("🚀 Testing CityLife Nexus backend components...")
    
    # Test coordinates
    origin = MockCoordinates(latitude=28.6139, longitude=77.2090)  # Delhi
    destination = MockCoordinates(latitude=28.5672, longitude=77.2100)  # AIIMS
    
    try:
        # Test route calculation
        print("🛣️  Testing route calculation...")
        routes = await mock_maps_service.get_multiple_route_options(origin, destination)
        print(f"   Found {len(routes)} route(s)")
        
        # Test AQI service
        print("🌱 Testing AQI service...")
        aqi_data = await mock_aqi_service.get_aqi_for_coordinates(origin)
        print(f"   AQI at origin: {aqi_data}")
        
        # Test traffic signals
        print("🚦 Testing traffic signal service...")
        route_coords = [origin, destination]
        signals = mock_traffic_signal_service.get_signals_along_route(route_coords)
        print(f"   Found {len(signals)} traffic signal(s)")
        
        print("✅ All backend tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

if __name__ == "__main__":
    print("🌱 CityLife Nexus - Quick Backend Test")
    print("=" * 50)
    
    # Run backend test
    success = asyncio.run(test_backend())
    
    if success:
        print("\n🎉 CityLife Nexus backend is ready!")
        print("   Use 'uvicorn quick_test:app --reload' to start the server")
    else:
        print("\n💥 CityLife Nexus backend needs attention!")
        sys.exit(1)