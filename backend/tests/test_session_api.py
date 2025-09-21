"""
Integration tests for session API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


def test_create_session_auto_generated(client):
    """Test creating a session with auto-generated ID"""
    response = client.post("/api/v1/sessions/create")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "session_id" in data
    assert data["session_id"].startswith("session_")
    assert data["vehicle_type"] == "car"
    assert data["total_trips"] == 0
    assert data["total_eco_score"] == 0


def test_create_session_custom_data(client):
    """Test creating a session with custom data"""
    session_data = {
        "session_id": "custom_test_session",
        "preferences": {
            "prioritize_time": 0.6,
            "prioritize_air_quality": 0.3,
            "voice_alerts_enabled": False
        },
        "health_profile": {
            "age_group": "senior",
            "respiratory_conditions": ["asthma"],
            "pollution_sensitivity": 2.0
        },
        "vehicle_type": "electric"
    }
    
    response = client.post("/api/v1/sessions/create", json=session_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["session_id"] == "custom_test_session"
    assert data["vehicle_type"] == "electric"
    assert data["preferences"]["prioritize_time"] == 0.6
    assert data["preferences"]["voice_alerts_enabled"] is False
    assert data["health_profile"]["age_group"] == "senior"


def test_create_duplicate_session(client):
    """Test creating a session with duplicate ID"""
    session_data = {
        "session_id": "duplicate_session",
        "vehicle_type": "car"
    }
    
    # First creation should succeed
    response1 = client.post("/api/v1/sessions/create", json=session_data)
    assert response1.status_code == 200
    
    # Second creation should fail
    response2 = client.post("/api/v1/sessions/create", json=session_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_get_session_by_id(client):
    """Test getting a session by ID"""
    # Create a session first
    session_data = {
        "session_id": "get_test_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Get the session
    response = client.get("/api/v1/sessions/get_test_session")
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "get_test_session"


def test_get_nonexistent_session(client):
    """Test getting a non-existent session"""
    response = client.get("/api/v1/sessions/nonexistent_session")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_current_session_info(client):
    """Test getting current session info with authentication"""
    # Create a session first
    session_data = {
        "session_id": "auth_test_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Get current session info with session ID in header
    headers = {"X-Session-ID": "auth_test_session"}
    response = client.get("/api/v1/sessions/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "auth_test_session"


def test_get_current_session_unauthorized(client):
    """Test getting current session info without authentication"""
    response = client.get("/api/v1/sessions/me")
    
    assert response.status_code == 401
    assert "session required" in response.json()["detail"].lower()


def test_update_current_session(client):
    """Test updating current session"""
    # Create a session first
    session_data = {
        "session_id": "update_test_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Update the session
    update_data = {
        "preferences": {
            "prioritize_time": 0.8,
            "voice_alerts_enabled": False
        },
        "vehicle_type": "electric"
    }
    
    headers = {"X-Session-ID": "update_test_session"}
    response = client.put("/api/v1/sessions/me", json=update_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_type"] == "electric"
    assert data["preferences"]["prioritize_time"] == 0.8
    assert data["preferences"]["voice_alerts_enabled"] is False


def test_update_preferences_only(client):
    """Test updating only preferences"""
    # Create a session first
    session_data = {
        "session_id": "prefs_update_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Update preferences only
    preferences_data = {
        "prioritize_time": 0.9,
        "prioritize_air_quality": 0.1,
        "max_detour_minutes": 20
    }
    
    headers = {"X-Session-ID": "prefs_update_session"}
    response = client.put("/api/v1/sessions/me/preferences", json=preferences_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["preferences"]["prioritize_time"] == 0.9
    assert data["preferences"]["max_detour_minutes"] == 20
    # Should preserve other preferences
    assert data["preferences"]["voice_alerts_enabled"] is True  # default


def test_update_health_profile_only(client):
    """Test updating only health profile"""
    # Create a session first
    session_data = {
        "session_id": "health_update_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Update health profile only
    health_data = {
        "age_group": "child",
        "respiratory_conditions": ["allergies", "asthma"],
        "pollution_sensitivity": 2.5,
        "activity_level": "high"
    }
    
    headers = {"X-Session-ID": "health_update_session"}
    response = client.put("/api/v1/sessions/me/health-profile", json=health_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["health_profile"]["age_group"] == "child"
    assert data["health_profile"]["respiratory_conditions"] == ["allergies", "asthma"]
    assert data["health_profile"]["pollution_sensitivity"] == 2.5


def test_record_trip_completion(client):
    """Test recording trip completion"""
    # Create a session first
    session_data = {
        "session_id": "trip_completion_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Record trip completion
    headers = {"X-Session-ID": "trip_completion_session"}
    response = client.post("/api/v1/sessions/me/trip-completed", headers=headers)
    
    assert response.status_code == 200
    assert "Trip count updated" in response.json()["message"]
    
    # Verify trip count was incremented
    get_response = client.get("/api/v1/sessions/me", headers=headers)
    assert get_response.json()["total_trips"] == 1


def test_add_eco_score(client):
    """Test adding eco score points"""
    # Create a session first
    session_data = {
        "session_id": "eco_score_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Add eco score points
    headers = {"X-Session-ID": "eco_score_session"}
    response = client.post("/api/v1/sessions/me/add-eco-score?points=75", headers=headers)
    
    assert response.status_code == 200
    assert "Added 75 eco score points" in response.json()["message"]
    
    # Verify eco score was added
    get_response = client.get("/api/v1/sessions/me", headers=headers)
    assert get_response.json()["total_eco_score"] == 75


def test_delete_current_session(client):
    """Test deleting current session"""
    # Create a session first
    session_data = {
        "session_id": "delete_current_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Delete the session
    headers = {"X-Session-ID": "delete_current_session"}
    response = client.delete("/api/v1/sessions/me", headers=headers)
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify session is gone
    get_response = client.get("/api/v1/sessions/delete_current_session")
    assert get_response.status_code == 404


def test_delete_session_by_id(client):
    """Test deleting session by ID"""
    # Create a session first
    session_data = {
        "session_id": "delete_by_id_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Delete the session by ID
    response = client.delete("/api/v1/sessions/delete_by_id_session")
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
    
    # Verify session is gone
    get_response = client.get("/api/v1/sessions/delete_by_id_session")
    assert get_response.status_code == 404


def test_authorization_header_auth(client):
    """Test authentication using Authorization header"""
    # Create a session first
    session_data = {
        "session_id": "bearer_auth_session",
        "vehicle_type": "car"
    }
    client.post("/api/v1/sessions/create", json=session_data)
    
    # Use Authorization header instead of X-Session-ID
    headers = {"Authorization": "Bearer bearer_auth_session"}
    response = client.get("/api/v1/sessions/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "bearer_auth_session"