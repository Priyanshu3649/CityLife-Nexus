"""
Unit tests for session service
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import UserSession
from app.services.session_service import SessionService, generate_session_id
from app.schemas.user import UserSessionCreate, UserSessionUpdate, UserPreferences, HealthProfile


# Test database setup
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def session_service(db_session):
    return SessionService(db_session)


def test_generate_session_id():
    """Test session ID generation"""
    session_id = generate_session_id()
    assert session_id.startswith("session_")
    assert len(session_id) == 24  # "session_" + 16 hex chars
    
    # Generate multiple IDs to ensure uniqueness
    ids = [generate_session_id() for _ in range(10)]
    assert len(set(ids)) == 10  # All should be unique


def test_create_session_with_defaults(session_service):
    """Test creating a session with default values"""
    session_data = UserSessionCreate(
        session_id="test_session_123",
        vehicle_type="car"
    )
    
    result = session_service.create_session(session_data)
    
    assert result.session_id == "test_session_123"
    assert result.vehicle_type == "car"
    assert result.total_trips == 0
    assert result.total_eco_score == 0
    assert result.preferences["prioritize_time"] == 0.4
    assert result.preferences["voice_alerts_enabled"] is True
    assert result.health_profile["age_group"] == "adult"


def test_create_session_with_custom_preferences(session_service):
    """Test creating a session with custom preferences"""
    preferences = UserPreferences(
        prioritize_time=0.6,
        prioritize_air_quality=0.3,
        prioritize_safety=0.1,
        voice_alerts_enabled=False,
        max_detour_minutes=15
    )
    
    health_profile = HealthProfile(
        age_group="senior",
        respiratory_conditions=["asthma"],
        pollution_sensitivity=2.0,
        activity_level="low"
    )
    
    session_data = UserSessionCreate(
        session_id="custom_session_456",
        preferences=preferences,
        health_profile=health_profile,
        vehicle_type="electric"
    )
    
    result = session_service.create_session(session_data)
    
    assert result.session_id == "custom_session_456"
    assert result.vehicle_type == "electric"
    assert result.preferences["prioritize_time"] == 0.6
    assert result.preferences["voice_alerts_enabled"] is False
    assert result.health_profile["age_group"] == "senior"
    assert result.health_profile["respiratory_conditions"] == ["asthma"]


def test_create_duplicate_session(session_service):
    """Test creating a session with duplicate ID raises error"""
    session_data = UserSessionCreate(
        session_id="duplicate_session",
        vehicle_type="car"
    )
    
    # First creation should succeed
    session_service.create_session(session_data)
    
    # Second creation should fail
    with pytest.raises(ValueError, match="already exists"):
        session_service.create_session(session_data)


def test_get_session(session_service):
    """Test retrieving a session"""
    # Create a session first
    session_data = UserSessionCreate(
        session_id="get_test_session",
        vehicle_type="car"
    )
    created = session_service.create_session(session_data)
    
    # Retrieve the session
    retrieved = session_service.get_session("get_test_session")
    
    assert retrieved is not None
    assert retrieved.session_id == created.session_id
    assert retrieved.id == created.id


def test_get_nonexistent_session(session_service):
    """Test retrieving a non-existent session returns None"""
    result = session_service.get_session("nonexistent_session")
    assert result is None


def test_update_session_preferences(session_service):
    """Test updating session preferences"""
    # Create a session
    session_data = UserSessionCreate(
        session_id="update_test_session",
        vehicle_type="car"
    )
    session_service.create_session(session_data)
    
    # Update preferences
    new_preferences = UserPreferences(
        prioritize_time=0.8,
        prioritize_air_quality=0.1,
        voice_alerts_enabled=False
    )
    
    update_data = UserSessionUpdate(preferences=new_preferences)
    updated = session_service.update_session("update_test_session", update_data)
    
    assert updated is not None
    assert updated.preferences["prioritize_time"] == 0.8
    assert updated.preferences["voice_alerts_enabled"] is False
    # Should preserve other existing preferences
    assert updated.preferences["prioritize_safety"] == 0.2  # default value


def test_update_session_health_profile(session_service):
    """Test updating session health profile"""
    # Create a session
    session_data = UserSessionCreate(
        session_id="health_update_session",
        vehicle_type="car"
    )
    session_service.create_session(session_data)
    
    # Update health profile
    new_health_profile = HealthProfile(
        age_group="child",
        respiratory_conditions=["allergies"],
        pollution_sensitivity=2.5
    )
    
    update_data = UserSessionUpdate(health_profile=new_health_profile)
    updated = session_service.update_session("health_update_session", update_data)
    
    assert updated is not None
    assert updated.health_profile["age_group"] == "child"
    assert updated.health_profile["respiratory_conditions"] == ["allergies"]
    assert updated.health_profile["pollution_sensitivity"] == 2.5


def test_increment_trip_count(session_service):
    """Test incrementing trip count"""
    # Create a session
    session_data = UserSessionCreate(
        session_id="trip_count_session",
        vehicle_type="car"
    )
    session_service.create_session(session_data)
    
    # Increment trip count
    success = session_service.increment_trip_count("trip_count_session")
    assert success is True
    
    # Verify the count was incremented
    updated_session = session_service.get_session("trip_count_session")
    assert updated_session.total_trips == 1
    
    # Increment again
    session_service.increment_trip_count("trip_count_session")
    updated_session = session_service.get_session("trip_count_session")
    assert updated_session.total_trips == 2


def test_add_eco_score(session_service):
    """Test adding eco score points"""
    # Create a session
    session_data = UserSessionCreate(
        session_id="eco_score_session",
        vehicle_type="car"
    )
    session_service.create_session(session_data)
    
    # Add eco score points
    success = session_service.add_eco_score("eco_score_session", 50)
    assert success is True
    
    # Verify the score was added
    updated_session = session_service.get_session("eco_score_session")
    assert updated_session.total_eco_score == 50
    
    # Add more points
    session_service.add_eco_score("eco_score_session", 25)
    updated_session = session_service.get_session("eco_score_session")
    assert updated_session.total_eco_score == 75


def test_get_or_create_session_existing(session_service):
    """Test get_or_create with existing session"""
    # Create a session first
    session_data = UserSessionCreate(
        session_id="existing_session",
        vehicle_type="electric"
    )
    created = session_service.create_session(session_data)
    
    # get_or_create should return existing session
    result = session_service.get_or_create_session("existing_session")
    
    assert result.id == created.id
    assert result.vehicle_type == "electric"


def test_get_or_create_session_new(session_service):
    """Test get_or_create with new session"""
    # get_or_create should create new session
    result = session_service.get_or_create_session("new_session")
    
    assert result.session_id == "new_session"
    assert result.vehicle_type == "car"  # default value
    assert result.total_trips == 0


def test_delete_session(session_service):
    """Test deleting a session"""
    # Create a session
    session_data = UserSessionCreate(
        session_id="delete_test_session",
        vehicle_type="car"
    )
    session_service.create_session(session_data)
    
    # Verify it exists
    assert session_service.get_session("delete_test_session") is not None
    
    # Delete the session
    success = session_service.delete_session("delete_test_session")
    assert success is True
    
    # Verify it's gone
    assert session_service.get_session("delete_test_session") is None


def test_delete_nonexistent_session(session_service):
    """Test deleting a non-existent session"""
    success = session_service.delete_session("nonexistent_session")
    assert success is False


def test_get_session_preferences(session_service):
    """Test getting session preferences"""
    preferences = UserPreferences(
        prioritize_time=0.7,
        voice_alerts_enabled=False
    )
    
    session_data = UserSessionCreate(
        session_id="prefs_test_session",
        preferences=preferences,
        vehicle_type="car"
    )
    session_service.create_session(session_data)
    
    # Get preferences
    result_prefs = session_service.get_session_preferences("prefs_test_session")
    
    assert result_prefs is not None
    assert result_prefs["prioritize_time"] == 0.7
    assert result_prefs["voice_alerts_enabled"] is False


def test_get_session_health_profile(session_service):
    """Test getting session health profile"""
    health_profile = HealthProfile(
        age_group="senior",
        respiratory_conditions=["copd"],
        pollution_sensitivity=3.0
    )
    
    session_data = UserSessionCreate(
        session_id="health_test_session",
        health_profile=health_profile,
        vehicle_type="car"
    )
    session_service.create_session(session_data)
    
    # Get health profile
    result_profile = session_service.get_session_health_profile("health_test_session")
    
    assert result_profile is not None
    assert result_profile["age_group"] == "senior"
    assert result_profile["respiratory_conditions"] == ["copd"]
    assert result_profile["pollution_sensitivity"] == 3.0