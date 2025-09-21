"""
Unit tests for Google Maps service
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.maps_service import GoogleMapsService
from app.schemas.base import CoordinatesSchema


@pytest.fixture
def maps_service():
    return GoogleMapsService()


@pytest.fixture
def sample_coordinates():
    return CoordinatesSchema(latitude=28.6139, longitude=77.2090)


@pytest.fixture
def sample_directions_response():
    """Mock Google Directions API response"""
    return {
        "status": "OK",
        "routes": [{
            "legs": [{
                "distance": {"value": 5000, "text": "5.0 km"},
                "duration": {"value": 900, "text": "15 mins"},
                "start_location": {"lat": 28.6139, "lng": 77.2090},
                "end_location": {"lat": 28.6200, "lng": 77.2150},
                "steps": [
                    {
                        "distance": {"value": 2500, "text": "2.5 km"},
                        "duration": {"value": 450, "text": "7 mins"},
                        "start_location": {"lat": 28.6139, "lng": 77.2090},
                        "end_location": {"lat": 28.6170, "lng": 77.2120}
                    },
                    {
                        "distance": {"value": 2500, "text": "2.5 km"},
                        "duration": {"value": 450, "text": "8 mins"},
                        "start_location": {"lat": 28.6170, "lng": 77.2120},
                        "end_location": {"lat": 28.6200, "lng": 77.2150}
                    }
                ]
            }]
        }]
    }


@pytest.fixture
def sample_geocoding_response():
    """Mock Google Geocoding API response"""
    return {
        "status": "OK",
        "results": [{
            "formatted_address": "New Delhi, Delhi, India",
            "geometry": {
                "location": {"lat": 28.6139, "lng": 77.2090}
            }
        }]
    }


class TestGoogleMapsService:
    
    @pytest.mark.asyncio
    async def test_geocode_address_success(self, maps_service, sample_geocoding_response):
        """Test successful address geocoding"""
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_geocoding_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.geocode_address("New Delhi, India")
            
            assert result is not None
            assert result.latitude == 28.6139
            assert result.longitude == 77.2090
            
            # Verify API call was made correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "address" in call_args[1]["params"]
            assert call_args[1]["params"]["address"] == "New Delhi, India"
    
    @pytest.mark.asyncio
    async def test_geocode_address_no_results(self, maps_service):
        """Test geocoding with no results"""
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"status": "ZERO_RESULTS", "results": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.geocode_address("Invalid Address")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_success(self, maps_service, sample_coordinates):
        """Test successful reverse geocoding"""
        reverse_response = {
            "status": "OK",
            "results": [{
                "formatted_address": "Connaught Place, New Delhi, Delhi, India"
            }]
        }
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = reverse_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.reverse_geocode(sample_coordinates)
            
            assert result == "Connaught Place, New Delhi, Delhi, India"
            
            # Verify API call parameters
            call_args = mock_get.call_args
            assert "latlng" in call_args[1]["params"]
            assert call_args[1]["params"]["latlng"] == "28.6139,77.209"
    
    @pytest.mark.asyncio
    async def test_get_directions_success(self, maps_service, sample_coordinates, sample_directions_response):
        """Test successful directions request"""
        destination = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_directions_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.get_directions(sample_coordinates, destination)
            
            assert result is not None
            assert result["status"] == "OK"
            assert len(result["routes"]) == 1
            
            # Verify API call parameters
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["origin"] == "28.6139,77.209"
            assert params["destination"] == "28.62,77.215"
            assert params["mode"] == "driving"
    
    @pytest.mark.asyncio
    async def test_get_directions_with_waypoints(self, maps_service, sample_coordinates, sample_directions_response):
        """Test directions request with waypoints"""
        destination = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        waypoints = [CoordinatesSchema(latitude=28.6170, longitude=77.2120)]
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_directions_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.get_directions(
                sample_coordinates, destination, waypoints=waypoints
            )
            
            assert result is not None
            
            # Verify waypoints parameter
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert "waypoints" in params
            assert params["waypoints"] == "28.617,77.212"
    
    @pytest.mark.asyncio
    async def test_get_directions_with_avoidances(self, maps_service, sample_coordinates, sample_directions_response):
        """Test directions request with avoidances"""
        destination = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_directions_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.get_directions(
                sample_coordinates, destination, avoid=["highways", "tolls"]
            )
            
            assert result is not None
            
            # Verify avoid parameter
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert "avoid" in params
            assert params["avoid"] == "highways|tolls"
    
    @pytest.mark.asyncio
    async def test_get_directions_with_departure_time(self, maps_service, sample_coordinates, sample_directions_response):
        """Test directions request with departure time"""
        destination = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        departure_time = datetime(2024, 1, 1, 9, 0, 0)
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_directions_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.get_directions(
                sample_coordinates, destination, departure_time=departure_time
            )
            
            assert result is not None
            
            # Verify departure_time parameter
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert "departure_time" in params
            assert isinstance(params["departure_time"], int)
    
    def test_parse_route_from_directions(self, maps_service, sample_directions_response):
        """Test parsing Google Directions response into RouteOption"""
        route = maps_service.parse_route_from_directions(sample_directions_response)
        
        assert route is not None
        assert route.distance_km == 5.0
        assert route.estimated_time_minutes == 15
        assert route.start_coords.latitude == 28.6139
        assert route.start_coords.longitude == 77.2090
        assert route.end_coords.latitude == 28.6200
        assert route.end_coords.longitude == 77.2150
        assert len(route.waypoints) == 3  # start + intermediate + end
        assert len(route.segments) == 2  # two steps in the response
        assert route.route_type == "optimal"
    
    def test_parse_route_empty_response(self, maps_service):
        """Test parsing empty directions response"""
        empty_response = {"status": "OK", "routes": []}
        
        route = maps_service.parse_route_from_directions(empty_response)
        
        assert route is None
    
    @pytest.mark.asyncio
    async def test_calculate_distance_matrix(self, maps_service):
        """Test distance matrix calculation"""
        origins = [CoordinatesSchema(latitude=28.6139, longitude=77.2090)]
        destinations = [CoordinatesSchema(latitude=28.6200, longitude=77.2150)]
        
        matrix_response = {
            "status": "OK",
            "rows": [{
                "elements": [{
                    "distance": {"value": 5000, "text": "5.0 km"},
                    "duration": {"value": 900, "text": "15 mins"},
                    "status": "OK"
                }]
            }]
        }
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = matrix_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.calculate_distance_matrix(origins, destinations)
            
            assert result is not None
            assert result["status"] == "OK"
            
            # Verify API call parameters
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["origins"] == "28.6139,77.209"
            assert params["destinations"] == "28.62,77.215"
    
    @pytest.mark.asyncio
    async def test_get_multiple_route_options(self, maps_service, sample_coordinates, sample_directions_response):
        """Test getting multiple route options"""
        destination = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_directions_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            routes = await maps_service.get_multiple_route_options(sample_coordinates, destination)
            
            # Should get up to 3 routes (fast, clean, toll_free)
            assert len(routes) >= 1
            assert len(routes) <= 3
            
            # Verify different route types
            route_types = [route.route_type for route in routes]
            assert "fast" in route_types
    
    @pytest.mark.asyncio
    async def test_get_traffic_conditions(self, maps_service, sample_coordinates):
        """Test getting traffic conditions"""
        result = await maps_service.get_traffic_conditions(sample_coordinates)
        
        assert result is not None
        assert "location" in result
        assert "traffic_level" in result
        assert "average_speed_kmh" in result
        assert result["location"]["latitude"] == sample_coordinates.latitude
        assert result["location"]["longitude"] == sample_coordinates.longitude
    
    def test_calculate_route_bounds(self, maps_service):
        """Test calculating route bounding box"""
        waypoints = [
            CoordinatesSchema(latitude=28.6139, longitude=77.2090),
            CoordinatesSchema(latitude=28.6200, longitude=77.2150),
            CoordinatesSchema(latitude=28.6100, longitude=77.2200)
        ]
        
        bounds = maps_service.calculate_route_bounds(waypoints)
        
        assert bounds["north"] == 28.6200
        assert bounds["south"] == 28.6100
        assert bounds["east"] == 77.2200
        assert bounds["west"] == 77.2090
    
    def test_calculate_route_bounds_empty(self, maps_service):
        """Test calculating bounds with empty waypoints"""
        bounds = maps_service.calculate_route_bounds([])
        
        assert bounds == {}
    
    def test_calculate_distance_between_points(self, maps_service):
        """Test distance calculation between two points"""
        point1 = CoordinatesSchema(latitude=28.6139, longitude=77.2090)
        point2 = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        
        distance = maps_service.calculate_distance_between_points(point1, point2)
        
        # Should be approximately 0.8 km between these points
        assert 0.5 < distance < 1.5
        assert isinstance(distance, float)
    
    def test_calculate_distance_same_points(self, maps_service):
        """Test distance calculation for same points"""
        point = CoordinatesSchema(latitude=28.6139, longitude=77.2090)
        
        distance = maps_service.calculate_distance_between_points(point, point)
        
        assert distance == 0.0
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, maps_service, sample_coordinates):
        """Test API error handling"""
        destination = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await maps_service.get_directions(sample_coordinates, destination)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_api_invalid_status(self, maps_service, sample_coordinates):
        """Test handling of invalid API status"""
        destination = CoordinatesSchema(latitude=28.6200, longitude=77.2150)
        
        with patch.object(maps_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"status": "REQUEST_DENIED", "routes": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await maps_service.get_directions(sample_coordinates, destination)
            
            assert result is None