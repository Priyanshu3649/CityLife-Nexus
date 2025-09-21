"""
Integration tests for traffic signal API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.models.base import Base
from app.core.database import get_db


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


class TestTrafficSignalAPI:
    
    def test_get_signal_current_state_valid(self, client):
        """Test getting current state of a valid signal"""
        response = client.get("/api/v1/signals/current/TL001")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["signal_id"] == "TL001"
        assert data["current_state"] in ["red", "yellow", "green"]
        assert data["cycle_time_seconds"] > 0
        assert data["time_to_next_change"] >= 0
        assert "coordinates" in data
        assert "is_coordinated" in data
    
    def test_get_signal_current_state_invalid(self, client):
        """Test getting state of non-existent signal"""
        response = client.get("/api/v1/signals/current/INVALID_ID")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_predict_signal_state_valid(self, client):
        """Test signal state prediction"""
        future_time = (datetime.utcnow() + timedelta(minutes=2)).isoformat()
        
        response = client.post(
            f"/api/v1/signals/predict/TL001?current_speed_kmh=50.0",
            json={"arrival_time": future_time}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["signal_id"] == "TL001"
        assert data["predicted_state"] in ["red", "yellow", "green"]
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["time_to_arrival"] >= 0
    
    def test_predict_signal_state_past_time(self, client):
        """Test prediction with past arrival time"""
        past_time = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
        
        response = client.post(
            f"/api/v1/signals/predict/TL001?current_speed_kmh=50.0",
            json={"arrival_time": past_time}
        )
        
        assert response.status_code == 400
        assert "must be in the future" in response.json()["detail"]
    
    def test_predict_signal_state_too_far_future(self, client):
        """Test prediction too far in the future"""
        far_future = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        
        response = client.post(
            f"/api/v1/signals/predict/TL001?current_speed_kmh=50.0",
            json={"arrival_time": far_future}
        )
        
        assert response.status_code == 400
        assert "too far in the future" in response.json()["detail"]
    
    def test_predict_signal_state_invalid_speed(self, client):
        """Test prediction with invalid speed"""
        future_time = (datetime.utcnow() + timedelta(minutes=2)).isoformat()
        
        response = client.post(
            f"/api/v1/signals/predict/TL001?current_speed_kmh=150.0",  # Too fast
            json={"arrival_time": future_time}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_nearby_signals(self, client):
        """Test getting nearby signals"""
        coordinates_data = {
            "latitude": 28.6304,
            "longitude": 77.2177
        }
        
        response = client.post(
            "/api/v1/signals/nearby?radius_km=2.0",
            json=coordinates_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should find at least one signal near Delhi coordinates
        if data:
            for signal in data:
                assert "signal_id" in signal
                assert "current_state" in signal
                assert "coordinates" in signal
    
    def test_get_nearby_signals_invalid_radius(self, client):
        """Test nearby signals with invalid radius"""
        coordinates_data = {
            "latitude": 28.6304,
            "longitude": 77.2177
        }
        
        response = client.post(
            "/api/v1/signals/nearby?radius_km=15.0",  # Too large
            json=coordinates_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_signals_along_route(self, client):
        """Test getting signals along a route"""
        route_data = [
            {"latitude": 28.6304, "longitude": 77.2177},
            {"latitude": 28.6289, "longitude": 77.2156},
            {"latitude": 28.6274, "longitude": 77.2135}
        ]
        
        response = client.post(
            "/api/v1/signals/along-route?buffer_meters=200.0",
            json=route_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should find signals along this route
        if data:
            signal_ids = [s["signal_id"] for s in data]
            # Should include some of the corridor_1 signals
            assert any(sid in ["TL001", "TL002", "TL003"] for sid in signal_ids)
    
    def test_get_signals_along_route_insufficient_coordinates(self, client):
        """Test route signals with insufficient coordinates"""
        route_data = [
            {"latitude": 28.6304, "longitude": 77.2177}
        ]
        
        response = client.post(
            "/api/v1/signals/along-route",
            json=route_data
        )
        
        assert response.status_code == 400
        assert "At least 2 coordinates required" in response.json()["detail"]
    
    def test_calculate_green_wave_valid_corridor(self, client):
        """Test green wave calculation for valid corridor"""
        response = client.get("/api/v1/signals/green-wave/corridor_1?average_speed_kmh=50.0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["corridor_id"] == "corridor_1"
        assert len(data["signals"]) >= 2
        assert data["optimal_speed_kmh"] == 50.0
        assert len(data["coordination_offset_seconds"]) > 0
        assert 0.0 <= data["success_probability"] <= 1.0
    
    def test_calculate_green_wave_invalid_corridor(self, client):
        """Test green wave for invalid corridor"""
        response = client.get("/api/v1/signals/green-wave/invalid_corridor?average_speed_kmh=50.0")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_calculate_green_wave_invalid_speed(self, client):
        """Test green wave with invalid speed"""
        response = client.get("/api/v1/signals/green-wave/corridor_1?average_speed_kmh=100.0")  # Too fast
        
        assert response.status_code == 422  # Validation error
    
    def test_optimize_corridor_timing_valid(self, client):
        """Test corridor timing optimization"""
        signal_chain = ["TL001", "TL002", "TL003"]
        
        response = client.post(
            "/api/v1/signals/optimize-corridor?traffic_density=moderate",
            json=signal_chain
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["signal_chain"] == signal_chain
        assert data["optimal_speed_kmh"] > 0
        assert data["total_distance_meters"] > 0
        assert data["coordination_efficiency"] > 0
        assert "recommended_offsets" in data
        assert data["traffic_density"] == "moderate"
    
    def test_optimize_corridor_timing_insufficient_signals(self, client):
        """Test corridor optimization with insufficient signals"""
        signal_chain = ["TL001"]
        
        response = client.post(
            "/api/v1/signals/optimize-corridor?traffic_density=moderate",
            json=signal_chain
        )
        
        assert response.status_code == 400
        assert "At least 2 signals required" in response.json()["detail"]
    
    def test_optimize_corridor_timing_too_many_signals(self, client):
        """Test corridor optimization with too many signals"""
        signal_chain = [f"TL{i:03d}" for i in range(1, 12)]  # 11 signals
        
        response = client.post(
            "/api/v1/signals/optimize-corridor?traffic_density=moderate",
            json=signal_chain
        )
        
        assert response.status_code == 400
        assert "Maximum 10 signals allowed" in response.json()["detail"]
    
    def test_optimize_corridor_timing_invalid_density(self, client):
        """Test corridor optimization with invalid traffic density"""
        signal_chain = ["TL001", "TL002"]
        
        response = client.post(
            "/api/v1/signals/optimize-corridor?traffic_density=extreme",
            json=signal_chain
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_simulate_adaptive_timing_valid(self, client):
        """Test adaptive timing simulation"""
        response = client.post(
            "/api/v1/signals/adaptive-timing/TL001?traffic_volume=150&pedestrian_count=10"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["signal_id"] == "TL001"
        assert "original_timing" in data
        assert "adaptive_timing" in data
        assert data["traffic_volume"] == 150
        assert data["pedestrian_count"] == 10
        assert "efficiency_gain_percent" in data
    
    def test_simulate_adaptive_timing_invalid_signal(self, client):
        """Test adaptive timing for invalid signal"""
        response = client.post(
            "/api/v1/signals/adaptive-timing/INVALID_ID?traffic_volume=100&pedestrian_count=5"
        )
        
        assert response.status_code == 404
        assert "Signal not found" in response.json()["detail"]
    
    def test_simulate_adaptive_timing_invalid_volume(self, client):
        """Test adaptive timing with invalid traffic volume"""
        response = client.post(
            "/api/v1/signals/adaptive-timing/TL001?traffic_volume=600&pedestrian_count=5"  # Too high
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_list_corridors(self, client):
        """Test listing all corridors"""
        response = client.get("/api/v1/signals/corridors")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_corridors" in data
        assert "corridors" in data
        assert data["total_corridors"] > 0
        
        for corridor in data["corridors"]:
            assert "corridor_id" in corridor
            assert "signal_count" in corridor
            assert "signal_ids" in corridor
            assert "performance" in corridor
    
    def test_get_corridor_performance_valid(self, client):
        """Test corridor performance metrics"""
        response = client.get("/api/v1/signals/corridor-performance/corridor_1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["corridor_id"] == "corridor_1"
        assert data["total_signals"] > 0
        assert data["coordination_percentage"] >= 0
        assert data["average_delay_seconds"] > 0
        assert data["throughput_vehicles_per_hour"] > 0
    
    def test_get_corridor_performance_invalid(self, client):
        """Test performance for invalid corridor"""
        response = client.get("/api/v1/signals/corridor-performance/invalid_corridor")
        
        assert response.status_code == 404
        assert "Corridor not found" in response.json()["detail"]
    
    def test_list_all_signals(self, client):
        """Test listing all signals"""
        response = client.get("/api/v1/signals/all-signals")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_signals" in data
        assert "signals" in data
        assert data["total_signals"] > 0
        
        for signal in data["signals"]:
            assert "signal_id" in signal
            assert "current_state" in signal
            assert "coordinates" in signal
    
    def test_initialize_signal_database(self, client):
        """Test database initialization"""
        response = client.post("/api/v1/signals/initialize-database")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "signals_created" in data
        assert "corridors_created" in data
        assert data["signals_created"] > 0
        assert data["corridors_created"] > 0
    
    def test_get_signal_detailed_info_valid(self, client):
        """Test getting detailed signal information"""
        response = client.get("/api/v1/signals/signal-info/TL001")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["signal_id"] == "TL001"
        assert "coordinates" in data
        assert "road_type" in data
        assert "timing" in data
        assert "coordination" in data
        assert "features" in data
        assert "current_state" in data
        
        # Check timing information
        timing = data["timing"]
        assert timing["cycle_time_seconds"] > 0
        assert timing["green_duration"] > 0
        assert timing["yellow_duration"] > 0
        assert timing["red_duration"] > 0
    
    def test_get_signal_detailed_info_invalid(self, client):
        """Test detailed info for invalid signal"""
        response = client.get("/api/v1/signals/signal-info/INVALID_ID")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_bulk_predict_signals_valid(self, client):
        """Test bulk signal prediction"""
        future_time = (datetime.utcnow() + timedelta(minutes=2)).isoformat()
        
        predictions_data = [
            {"signal_id": "TL001", "arrival_time": future_time},
            {"signal_id": "TL002", "arrival_time": future_time},
            {"signal_id": "TL003", "arrival_time": future_time}
        ]
        
        response = client.post(
            "/api/v1/signals/bulk-predict?current_speed_kmh=50.0",
            json=predictions_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requests"] == 3
        assert data["successful_predictions"] >= 0
        assert len(data["results"]) == 3
        
        for result in data["results"]:
            assert "signal_id" in result
            assert "status" in result
            if result["status"] == "success":
                assert "prediction" in result
                assert result["prediction"]["signal_id"] == result["signal_id"]
    
    def test_bulk_predict_signals_too_many(self, client):
        """Test bulk prediction with too many requests"""
        future_time = (datetime.utcnow() + timedelta(minutes=2)).isoformat()
        
        predictions_data = [
            {"signal_id": f"TL{i:03d}", "arrival_time": future_time}
            for i in range(1, 22)  # 21 predictions
        ]
        
        response = client.post(
            "/api/v1/signals/bulk-predict?current_speed_kmh=50.0",
            json=predictions_data
        )
        
        assert response.status_code == 400
        assert "Maximum 20 signal predictions allowed" in response.json()["detail"]
    
    def test_bulk_predict_signals_mixed_results(self, client):
        """Test bulk prediction with mix of valid and invalid signals"""
        future_time = (datetime.utcnow() + timedelta(minutes=2)).isoformat()
        
        predictions_data = [
            {"signal_id": "TL001", "arrival_time": future_time},
            {"signal_id": "INVALID_ID", "arrival_time": future_time},
            {"signal_id": "TL002", "arrival_time": "invalid_time"}
        ]
        
        response = client.post(
            "/api/v1/signals/bulk-predict?current_speed_kmh=50.0",
            json=predictions_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requests"] == 3
        
        # Check that we have different statuses
        statuses = [result["status"] for result in data["results"]]
        assert "success" in statuses or "not_found" in statuses
        assert "error" in statuses or "not_found" in statuses