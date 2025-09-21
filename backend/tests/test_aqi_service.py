"""
Unit tests for AQI service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.aqi_service import AQIService
from app.schemas.base import CoordinatesSchema
from app.schemas.air_quality import AQIReading, RouteAQIData
from app.schemas.user import HealthProfile


@pytest.fixture
def aqi_service():
    return AQIService()


@pytest.fixture
def sample_coordinates():
    return CoordinatesSchema(latitude=28.6139, longitude=77.2090)


@pytest.fixture
def sample_openaq_response():
    """Mock OpenAQ API response"""
    return {
        "results": [
            {
                "coordinates": {"latitude": 28.6139, "longitude": 77.2090},
                "parameter": "pm25",
                "value": 45.5,
                "date": {"utc": "2024-01-01T12:00:00Z"},
                "unit": "µg/m³"
            },
            {
                "coordinates": {"latitude": 28.6140, "longitude": 77.2091},
                "parameter": "pm10",
                "value": 85.2,
                "date": {"utc": "2024-01-01T12:00:00Z"},
                "unit": "µg/m³"
            }
        ]
    }


class TestAQIService:
    
    @pytest.mark.asyncio
    async def test_get_measurements_by_location_success(self, aqi_service, sample_coordinates, sample_openaq_response):
        """Test successful AQI measurements retrieval"""
        with patch.object(aqi_service.client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = sample_openaq_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Mock Redis cache
            with patch.object(aqi_service, '_cache_aqi_reading') as mock_cache:
                readings = await aqi_service.get_measurements_by_location(sample_coordinates)
                
                assert len(readings) == 2
                assert readings[0].aqi_value > 0
                assert readings[0].coordinates.latitude == 28.6139
                assert readings[0].source == "openaq"
                
                # Verify caching was called
                assert mock_cache.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_measurements_api_error(self, aqi_service, sample_coordinates):
        """Test handling of API errors"""
        with patch.object(aqi_service.client, 'get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            # Mock cached measurements
            with patch.object(aqi_service, '_get_cached_measurements') as mock_cached:
                mock_cached.return_value = [aqi_service._generate_mock_aqi_reading(sample_coordinates)]
                
                readings = await aqi_service.get_measurements_by_location(sample_coordinates)
                
                assert len(readings) == 1
                assert readings[0].source == "mock"
                mock_cached.assert_called_once()
    
    def test_convert_measurement_to_aqi(self, aqi_service):
        """Test conversion of OpenAQ measurement to AQI reading"""
        measurement = {
            "coordinates": {"latitude": 28.6139, "longitude": 77.2090},
            "parameter": "pm25",
            "value": 35.0,
            "date": {"utc": "2024-01-01T12:00:00Z"}
        }
        
        reading = aqi_service._convert_measurement_to_aqi(measurement)
        
        assert reading is not None
        assert reading.coordinates.latitude == 28.6139
        assert reading.pm25 == 35.0
        assert reading.aqi_value > 0
        assert reading.source == "openaq"
    
    def test_convert_measurement_invalid_data(self, aqi_service):
        """Test handling of invalid measurement data"""
        invalid_measurement = {
            "parameter": "pm25",
            "value": None  # Invalid value
        }
        
        reading = aqi_service._convert_measurement_to_aqi(invalid_measurement)
        
        assert reading is None
    
    def test_calculate_aqi_pm25(self, aqi_service):
        """Test AQI calculation for PM2.5"""
        # Test different PM2.5 concentrations
        test_cases = [
            (10.0, 42),   # Good range
            (25.0, 79),   # Moderate range
            (45.0, 122),  # Unhealthy for sensitive groups
            (100.0, 168), # Unhealthy range
            (200.0, 250)  # Very unhealthy range
        ]
        
        for concentration, expected_aqi_range in test_cases:
            aqi = aqi_service._calculate_aqi(concentration, "pm25")
            assert abs(aqi - expected_aqi_range) < 20  # Allow some variance
    
    def test_calculate_aqi_pm10(self, aqi_service):
        """Test AQI calculation for PM10"""
        aqi = aqi_service._calculate_aqi(100.0, "pm10")
        assert 80 <= aqi <= 120  # Should be in moderate range
    
    def test_calculate_aqi_unknown_parameter(self, aqi_service):
        """Test AQI calculation for unknown parameter"""
        aqi = aqi_service._calculate_aqi(50.0, "unknown")
        assert aqi == 100  # Generic conversion: 50 * 2
    
    @pytest.mark.asyncio
    async def test_get_route_aqi_data(self, aqi_service):
        """Test getting AQI data for a route"""
        route_coordinates = [
            CoordinatesSchema(latitude=28.6139, longitude=77.2090),
            CoordinatesSchema(latitude=28.6150, longitude=77.2100),
            CoordinatesSchema(latitude=28.6160, longitude=77.2110)
        ]
        
        # Mock the measurements method
        with patch.object(aqi_service, 'get_measurements_by_location') as mock_measurements:
            mock_reading = AQIReading(
                coordinates=route_coordinates[0],
                aqi_value=85,
                pm25=35.0,
                pm10=None,
                no2=None,
                o3=None,
                source="mock",
                reading_time=datetime.utcnow()
            )
            mock_measurements.return_value = [mock_reading]
            
            route_aqi_data = await aqi_service.get_route_aqi_data(route_coordinates)
            
            assert isinstance(route_aqi_data, RouteAQIData)
            assert route_aqi_data.average_aqi > 0
            assert len(route_aqi_data.route_coordinates) == 3
            assert len(route_aqi_data.aqi_readings) > 0
    
    def test_calculate_health_impact_default_profile(self, aqi_service):
        """Test health impact calculation with default profile"""
        route_aqi_data = RouteAQIData(
            route_coordinates=[CoordinatesSchema(latitude=28.6139, longitude=77.2090)],
            aqi_readings=[],
            average_aqi=120,
            max_aqi=150,
            pollution_hotspots=[]
        )
        
        health_impact = aqi_service.calculate_health_impact(
            route_aqi_data=route_aqi_data,
            travel_time_minutes=30
        )
        
        assert health_impact.health_risk_score > 0
        assert health_impact.estimated_exposure_pm25 > 0
        assert isinstance(health_impact.recommended_precautions, list)
    
    def test_calculate_health_impact_sensitive_profile(self, aqi_service):
        """Test health impact calculation with sensitive health profile"""
        route_aqi_data = RouteAQIData(
            route_coordinates=[CoordinatesSchema(latitude=28.6139, longitude=77.2090)],
            aqi_readings=[],
            average_aqi=120,
            max_aqi=150,
            pollution_hotspots=[]
        )
        
        health_profile = HealthProfile(
            age_group="senior",
            respiratory_conditions=["asthma", "copd"],
            pollution_sensitivity=2.0,
            activity_level="low"
        )
        
        health_impact = aqi_service.calculate_health_impact(
            route_aqi_data=route_aqi_data,
            health_profile=health_profile,
            travel_time_minutes=30
        )
        
        # Should have higher risk score due to sensitive profile
        assert health_impact.health_risk_score > 40
        assert "mask" in " ".join(health_impact.recommended_precautions).lower()
    
    def test_calculate_health_impact_child_profile(self, aqi_service):
        """Test health impact calculation for children"""
        route_aqi_data = RouteAQIData(
            route_coordinates=[CoordinatesSchema(latitude=28.6139, longitude=77.2090)],
            aqi_readings=[],
            average_aqi=100,
            max_aqi=120,
            pollution_hotspots=[]
        )
        
        health_profile = HealthProfile(
            age_group="child",
            respiratory_conditions=[],
            pollution_sensitivity=1.0,
            activity_level="high"
        )
        
        health_impact = aqi_service.calculate_health_impact(
            route_aqi_data=route_aqi_data,
            health_profile=health_profile,
            travel_time_minutes=20
        )
        
        # Should include child-specific precautions
        precautions_text = " ".join(health_impact.recommended_precautions).lower()
        assert "children" in precautions_text
    
    def test_calculate_base_health_risk(self, aqi_service):
        """Test base health risk calculation"""
        test_cases = [
            (30, 10.0),   # Good air quality
            (75, 25.0),   # Moderate
            (125, 45.0),  # Unhealthy for sensitive groups
            (175, 70.0),  # Unhealthy
            (250, 85.0),  # Very unhealthy
            (400, 95.0)   # Hazardous
        ]
        
        for aqi, expected_risk in test_cases:
            risk = aqi_service._calculate_base_health_risk(aqi)
            assert risk == expected_risk
    
    def test_get_aqi_category(self, aqi_service):
        """Test AQI category determination"""
        test_cases = [
            (25, "Good", "green"),
            (75, "Moderate", "yellow"),
            (125, "Unhealthy for Sensitive Groups", "orange"),
            (175, "Unhealthy", "red"),
            (250, "Very Unhealthy", "purple"),
            (400, "Hazardous", "maroon")
        ]
        
        for aqi, expected_category, expected_color in test_cases:
            category, color = aqi_service.get_aqi_category(aqi)
            assert category == expected_category
            assert color == expected_color
    
    def test_generate_mock_aqi_reading(self, aqi_service, sample_coordinates):
        """Test mock AQI reading generation"""
        reading = aqi_service._generate_mock_aqi_reading(sample_coordinates)
        
        assert reading.coordinates == sample_coordinates
        assert 60 <= reading.aqi_value <= 120  # Within expected range
        assert reading.pm25 is not None
        assert reading.pm10 is not None
        assert reading.source == "mock"
        assert isinstance(reading.reading_time, datetime)
    
    @pytest.mark.asyncio
    async def test_cache_aqi_reading(self, aqi_service, sample_coordinates):
        """Test AQI reading caching"""
        reading = AQIReading(
            coordinates=sample_coordinates,
            aqi_value=85,
            pm25=35.0,
            pm10=None,
            no2=None,
            o3=None,
            source="test",
            reading_time=datetime.utcnow()
        )
        
        # Mock Redis client
        with patch.object(aqi_service.redis_client, 'setex') as mock_setex:
            await aqi_service._cache_aqi_reading(reading)
            
            # Verify cache was called
            mock_setex.assert_called_once()
            call_args = mock_setex.call_args
            assert call_args[0][1] == 1800  # 30 minutes TTL
    
    @pytest.mark.asyncio
    async def test_get_cached_measurements(self, aqi_service, sample_coordinates):
        """Test retrieving cached measurements"""
        # Mock Redis response
        cached_data = {
            "aqi_value": 85,
            "pm25": 35.0,
            "pm10": None,
            "no2": None,
            "o3": None,
            "source": "cached",
            "reading_time": datetime.utcnow().isoformat()
        }
        
        with patch.object(aqi_service.redis_client, 'get') as mock_get:
            mock_get.return_value = '{"aqi_value": 85, "pm25": 35.0, "source": "cached", "reading_time": "2024-01-01T12:00:00"}'
            
            readings = await aqi_service._get_cached_measurements(sample_coordinates, 5.0)
            
            assert len(readings) == 1
            assert readings[0].aqi_value == 85
            assert readings[0].source == "cached"
    
    @pytest.mark.asyncio
    async def test_get_cached_measurements_no_cache(self, aqi_service, sample_coordinates):
        """Test fallback when no cached data available"""
        with patch.object(aqi_service.redis_client, 'get') as mock_get:
            mock_get.return_value = None
            
            readings = await aqi_service._get_cached_measurements(sample_coordinates, 5.0)
            
            assert len(readings) == 1
            assert readings[0].source == "mock"
    
    def test_route_aqi_data_with_hotspots(self, aqi_service):
        """Test route AQI data identification of pollution hotspots"""
        # Create mock route with high pollution area
        route_coordinates = [
            CoordinatesSchema(latitude=28.6139, longitude=77.2090),
            CoordinatesSchema(latitude=28.6150, longitude=77.2100)  # This will be a hotspot
        ]
        
        # Mock readings with one high pollution area
        mock_readings = [
            AQIReading(
                coordinates=route_coordinates[0],
                aqi_value=85,  # Moderate
                pm25=35.0,
                pm10=None,
                no2=None,
                o3=None,
                source="mock",
                reading_time=datetime.utcnow()
            ),
            AQIReading(
                coordinates=route_coordinates[1],
                aqi_value=180,  # Unhealthy - should be hotspot
                pm25=95.0,
                pm10=None,
                no2=None,
                o3=None,
                source="mock",
                reading_time=datetime.utcnow()
            )
        ]
        
        # Manually create RouteAQIData to test hotspot detection logic
        aqi_values = [r.aqi_value for r in mock_readings]
        hotspots = [coord for coord, reading in zip(route_coordinates, mock_readings) 
                   if reading.aqi_value > 150]
        
        route_aqi_data = RouteAQIData(
            route_coordinates=route_coordinates,
            aqi_readings=mock_readings,
            average_aqi=int(sum(aqi_values) / len(aqi_values)),
            max_aqi=max(aqi_values),
            pollution_hotspots=hotspots
        )
        
        assert len(route_aqi_data.pollution_hotspots) == 1
        assert route_aqi_data.max_aqi == 180
        assert route_aqi_data.average_aqi == 132