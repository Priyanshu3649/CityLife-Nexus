"""
Integration tests for AQI API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from app.main import app
from app.models.base import Base
from app.core.database import get_db
from app.services.aqi_service import aqi_service


# Test database setup
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    return TestClient(app)


@pytest.fixture
def mock_aqi_readings():
    """Mock AQI readings for testing"""
    from app.schemas.air_quality import AQIReading
    from app.schemas.base import CoordinatesSchema
    from datetime import datetime
    
    return [
        AQIReading(
            coordinates=CoordinatesSchema(latitude=28.6139, longitude=77.2090),
            aqi_value=85,
            pm25=35.0,
            pm10=65.0,
            no2=25.0,
            o3=45.0,
            source="openaq",
            reading_time=datetime.utcnow()
        ),
        AQIReading(
            coordinates=CoordinatesSchema(latitude=28.6140, longitude=77.2091),
            aqi_value=120,
            pm25=55.0,
            pm10=85.0,
            no2=35.0,
            o3=65.0,
            source="openaq",
            reading_time=datetime.utcnow()
        )
    ]


class TestAQIAPI:
    
    def test_get_aqi_measurements(self, client, mock_aqi_readings):
        """Test getting AQI measurements"""
        coordinates_data = {
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        with patch.object(aqi_service, 'get_measurements_by_location') as mock_get:
            with patch.object(aqi_service, 'store_aqi_reading') as mock_store:
                mock_get.return_value = mock_aqi_readings
                
                response = client.post(
                    "/api/v1/aqi/measurements",
                    json=coordinates_data,
                    params={"radius_km": 5.0, "parameter": "pm25"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert len(data) == 2
                assert data[0]["aqi_value"] == 85
                assert data[0]["coordinates"]["latitude"] == 28.6139
                assert data[0]["source"] == "openaq"
                
                # Verify storage was called
                assert mock_store.call_count == 2
    
    def test_analyze_route_aqi(self, client):
        """Test route AQI analysis"""
        route_data = [
            {"latitude": 28.6139, "longitude": 77.2090},
            {"latitude": 28.6150, "longitude": 77.2100},
            {"latitude": 28.6160, "longitude": 77.2110}
        ]
        
        from app.schemas.air_quality import RouteAQIData
        from app.schemas.base import CoordinatesSchema
        
        mock_route_aqi = RouteAQIData(
            route_coordinates=[CoordinatesSchema(**coord) for coord in route_data],
            aqi_readings=[],
            average_aqi=95,
            max_aqi=120,
            pollution_hotspots=[]
        )
        
        with patch.object(aqi_service, 'get_route_aqi_data') as mock_get:
            mock_get.return_value = mock_route_aqi
            
            response = client.post(
                "/api/v1/aqi/route-analysis",
                json=route_data,
                params={"radius_km": 2.0}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["average_aqi"] == 95
            assert data["max_aqi"] == 120
            assert len(data["route_coordinates"]) == 3
    
    def test_analyze_route_aqi_invalid_coordinates(self, client):
        """Test route analysis with insufficient coordinates"""
        route_data = [
            {"latitude": 28.6139, "longitude": 77.2090}
        ]
        
        response = client.post(
            "/api/v1/aqi/route-analysis",
            json=route_data
        )
        
        assert response.status_code == 400
        assert "At least 2 coordinates required" in response.json()["detail"]
    
    def test_analyze_route_aqi_too_many_coordinates(self, client):
        """Test route analysis with too many coordinates"""
        route_data = [
            {"latitude": 28.6139 + i*0.001, "longitude": 77.2090 + i*0.001}
            for i in range(101)  # 101 coordinates
        ]
        
        response = client.post(
            "/api/v1/aqi/route-analysis",
            json=route_data
        )
        
        assert response.status_code == 400
        assert "Maximum 100 coordinates allowed" in response.json()["detail"]
    
    def test_calculate_health_impact_no_session(self, client):
        """Test health impact calculation without user session"""
        route_data = [
            {"latitude": 28.6139, "longitude": 77.2090},
            {"latitude": 28.6150, "longitude": 77.2100}
        ]
        
        from app.schemas.air_quality import RouteAQIData, HealthImpactEstimate
        from app.schemas.base import CoordinatesSchema
        
        mock_route_aqi = RouteAQIData(
            route_coordinates=[CoordinatesSchema(**coord) for coord in route_data],
            aqi_readings=[],
            average_aqi=110,
            max_aqi=130,
            pollution_hotspots=[]
        )
        
        mock_health_impact = HealthImpactEstimate(
            estimated_exposure_pm25=25.5,
            health_risk_score=45.0,
            recommended_precautions=["Limit outdoor activities"],
            comparison_to_baseline=15.2
        )
        
        with patch.object(aqi_service, 'get_route_aqi_data') as mock_route:
            with patch.object(aqi_service, 'calculate_health_impact') as mock_health:
                mock_route.return_value = mock_route_aqi
                mock_health.return_value = mock_health_impact
                
                response = client.post(
                    "/api/v1/aqi/health-impact",
                    json=route_data,
                    params={"travel_time_minutes": 30}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["health_risk_score"] == 45.0
                assert data["estimated_exposure_pm25"] == 25.5
                assert "Limit outdoor activities" in data["recommended_precautions"]
    
    def test_calculate_health_impact_with_session(self, client):
        """Test health impact calculation with user session"""
        # First create a session
        session_data = {
            "session_id": "health_test_session",
            "health_profile": {
                "age_group": "senior",
                "respiratory_conditions": ["asthma"],
                "pollution_sensitivity": 2.0,
                "activity_level": "low"
            },
            "vehicle_type": "car"
        }
        client.post("/api/v1/sessions/create", json=session_data)
        
        route_data = [
            {"latitude": 28.6139, "longitude": 77.2090},
            {"latitude": 28.6150, "longitude": 77.2100}
        ]
        
        from app.schemas.air_quality import RouteAQIData, HealthImpactEstimate
        from app.schemas.base import CoordinatesSchema
        
        mock_route_aqi = RouteAQIData(
            route_coordinates=[CoordinatesSchema(**coord) for coord in route_data],
            aqi_readings=[],
            average_aqi=110,
            max_aqi=130,
            pollution_hotspots=[]
        )
        
        mock_health_impact = HealthImpactEstimate(
            estimated_exposure_pm25=35.5,
            health_risk_score=65.0,  # Higher due to sensitive profile
            recommended_precautions=["Consider wearing a mask", "Limit outdoor activities"],
            comparison_to_baseline=25.2
        )
        
        with patch.object(aqi_service, 'get_route_aqi_data') as mock_route:
            with patch.object(aqi_service, 'calculate_health_impact') as mock_health:
                mock_route.return_value = mock_route_aqi
                mock_health.return_value = mock_health_impact
                
                headers = {"X-Session-ID": "health_test_session"}
                response = client.post(
                    "/api/v1/aqi/health-impact",
                    json=route_data,
                    params={"travel_time_minutes": 30},
                    headers=headers
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["health_risk_score"] == 65.0
                assert "mask" in " ".join(data["recommended_precautions"]).lower()
    
    def test_get_aqi_category(self, client):
        """Test AQI category endpoint"""
        response = client.get("/api/v1/aqi/category?aqi_value=85")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["aqi_value"] == 85
        assert data["category"] == "Moderate"
        assert data["color"] == "yellow"
        assert "health_message" in data
    
    def test_get_aqi_category_invalid_value(self, client):
        """Test AQI category with invalid value"""
        response = client.get("/api/v1/aqi/category?aqi_value=600")
        
        assert response.status_code == 422  # Validation error
    
    def test_compare_route_air_quality(self, client):
        """Test comparing air quality between two routes"""
        route1_data = [
            {"latitude": 28.6139, "longitude": 77.2090},
            {"latitude": 28.6150, "longitude": 77.2100}
        ]
        
        route2_data = [
            {"latitude": 28.6139, "longitude": 77.2090},
            {"latitude": 28.6155, "longitude": 77.2105}
        ]
        
        from app.schemas.air_quality import RouteAQIData, HealthImpactEstimate
        from app.schemas.base import CoordinatesSchema
        
        # Mock route 1 (cleaner)
        mock_route1_aqi = RouteAQIData(
            route_coordinates=[CoordinatesSchema(**coord) for coord in route1_data],
            aqi_readings=[],
            average_aqi=85,
            max_aqi=100,
            pollution_hotspots=[]
        )
        
        # Mock route 2 (more polluted)
        mock_route2_aqi = RouteAQIData(
            route_coordinates=[CoordinatesSchema(**coord) for coord in route2_data],
            aqi_readings=[],
            average_aqi=120,
            max_aqi=140,
            pollution_hotspots=[]
        )
        
        mock_impact1 = HealthImpactEstimate(
            estimated_exposure_pm25=20.0,
            health_risk_score=35.0,
            recommended_precautions=[],
            comparison_to_baseline=10.0
        )
        
        mock_impact2 = HealthImpactEstimate(
            estimated_exposure_pm25=30.0,
            health_risk_score=50.0,
            recommended_precautions=["Limit outdoor activities"],
            comparison_to_baseline=25.0
        )
        
        with patch.object(aqi_service, 'get_route_aqi_data') as mock_route:
            with patch.object(aqi_service, 'calculate_health_impact') as mock_health:
                # Return different data based on call order
                mock_route.side_effect = [mock_route1_aqi, mock_route2_aqi]
                mock_health.side_effect = [mock_impact1, mock_impact2]
                
                response = client.post(
                    "/api/v1/aqi/compare-routes",
                    json={
                        "route1_coordinates": route1_data,
                        "route2_coordinates": route2_data
                    },
                    params={
                        "travel_time1_minutes": 25,
                        "travel_time2_minutes": 30
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["recommendation"] == "route1"
                assert "better air quality" in data["reason"]
                assert data["route1"]["aqi_data"]["average_aqi"] == 85
                assert data["route2"]["aqi_data"]["average_aqi"] == 120
                assert data["pollution_exposure_difference"] == 10.0
    
    def test_get_current_air_quality(self, client, mock_aqi_readings):
        """Test getting current air quality conditions"""
        with patch.object(aqi_service, 'get_measurements_by_location') as mock_get:
            with patch.object(aqi_service, 'store_aqi_reading') as mock_store:
                mock_get.return_value = mock_aqi_readings
                
                response = client.get(
                    "/api/v1/aqi/current-conditions",
                    params={"latitude": 28.6139, "longitude": 77.2090}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["current_aqi"] == 120  # Latest reading (max by time)
                assert data["category"] == "Unhealthy for Sensitive Groups"
                assert data["color"] == "orange"
                assert "pollutants" in data
                assert data["pollutants"]["pm25"] == 55.0
                assert "health_message" in data
    
    def test_get_current_air_quality_no_data(self, client):
        """Test current air quality when no data available"""
        with patch.object(aqi_service, 'get_measurements_by_location') as mock_get:
            mock_get.return_value = []
            
            response = client.get(
                "/api/v1/aqi/current-conditions",
                params={"latitude": 28.6139, "longitude": 77.2090}
            )
            
            assert response.status_code == 404
            assert "No air quality data available" in response.json()["detail"]
    
    def test_health_impact_invalid_travel_time(self, client):
        """Test health impact with invalid travel time"""
        route_data = [
            {"latitude": 28.6139, "longitude": 77.2090},
            {"latitude": 28.6150, "longitude": 77.2100}
        ]
        
        response = client.post(
            "/api/v1/aqi/health-impact",
            json=route_data,
            params={"travel_time_minutes": 0}  # Invalid: must be >= 1
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_measurements_invalid_radius(self, client):
        """Test measurements with invalid radius"""
        coordinates_data = {
            "latitude": 28.6139,
            "longitude": 77.2090
        }
        
        response = client.post(
            "/api/v1/aqi/measurements",
            json=coordinates_data,
            params={"radius_km": 100.0}  # Invalid: max is 50.0
        )
        
        assert response.status_code == 422  # Validation error