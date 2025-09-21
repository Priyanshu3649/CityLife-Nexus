"""
Unit tests for data models
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import UserSession, UserAchievement
from app.models.traffic import TrafficSignal, Route
from app.models.air_quality import AQIReading, WeatherData
from app.models.emergency import EmergencyAlert, IncidentReport
from app.models.analytics import TripMetrics, ParkingSpace, ChargingStation


# Test database setup
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_user_session_creation(db_session):
    """Test UserSession model creation and validation"""
    user_session = UserSession(
        session_id="test_session_123",
        preferences={"prioritize_time": 0.5, "prioritize_air_quality": 0.3},
        health_profile={"age_group": "adult", "respiratory_conditions": []},
        vehicle_type="car"
    )
    
    db_session.add(user_session)
    db_session.commit()
    
    # Verify the user session was created
    retrieved = db_session.query(UserSession).filter_by(session_id="test_session_123").first()
    assert retrieved is not None
    assert retrieved.session_id == "test_session_123"
    assert retrieved.vehicle_type == "car"
    assert retrieved.total_trips == 0


def test_traffic_signal_creation(db_session):
    """Test TrafficSignal model creation and validation"""
    signal = TrafficSignal(
        signal_id="TL001",
        latitude=28.6139,
        longitude=77.2090,
        cycle_time_seconds=120,
        green_duration=60,
        red_duration=55,
        current_state="green"
    )
    
    db_session.add(signal)
    db_session.commit()
    
    # Verify the signal was created
    retrieved = db_session.query(TrafficSignal).filter_by(signal_id="TL001").first()
    assert retrieved is not None
    assert retrieved.signal_id == "TL001"
    assert retrieved.cycle_time_seconds == 120
    assert retrieved.current_state == "green"


def test_route_creation(db_session):
    """Test Route model creation and validation"""
    route = Route(
        start_lat=28.6139,
        start_lng=77.2090,
        end_lat=28.6145,
        end_lng=77.2095,
        distance_km=2.5,
        estimated_time_minutes=15,
        average_aqi=85,
        route_score=7.5,
        route_type="optimal"
    )
    
    db_session.add(route)
    db_session.commit()
    
    # Verify the route was created
    retrieved = db_session.query(Route).first()
    assert retrieved is not None
    assert retrieved.distance_km == 2.5
    assert retrieved.route_type == "optimal"


def test_aqi_reading_creation(db_session):
    """Test AQIReading model creation and validation"""
    from datetime import datetime
    
    aqi_reading = AQIReading(
        latitude=28.6139,
        longitude=77.2090,
        aqi_value=150,
        pm25=75.5,
        pm10=120.0,
        source="openaq",
        reading_time=datetime.utcnow()
    )
    
    db_session.add(aqi_reading)
    db_session.commit()
    
    # Verify the reading was created
    retrieved = db_session.query(AQIReading).first()
    assert retrieved is not None
    assert retrieved.aqi_value == 150
    assert retrieved.source == "openaq"


def test_emergency_alert_creation(db_session):
    """Test EmergencyAlert model creation and validation"""
    alert = EmergencyAlert(
        alert_type="accident",
        latitude=28.6139,
        longitude=77.2090,
        radius_km=1.5,
        severity=3,
        message="Traffic accident on main road",
        is_active=True,
        created_by="system"
    )
    
    db_session.add(alert)
    db_session.commit()
    
    # Verify the alert was created
    retrieved = db_session.query(EmergencyAlert).first()
    assert retrieved is not None
    assert retrieved.alert_type == "accident"
    assert retrieved.severity == 3
    assert retrieved.is_active is True


def test_trip_metrics_creation(db_session):
    """Test TripMetrics model creation and validation"""
    import uuid
    
    # First create a user session and route
    user_session = UserSession(session_id="test_session")
    route = Route(
        start_lat=28.6139, start_lng=77.2090,
        end_lat=28.6145, end_lng=77.2095,
        distance_km=2.5, estimated_time_minutes=15
    )
    
    db_session.add(user_session)
    db_session.add(route)
    db_session.commit()
    
    # Create trip metrics
    trip_metrics = TripMetrics(
        trip_id=uuid.uuid4(),
        user_session_id=user_session.id,
        route_id=route.id,
        actual_travel_time=900,  # 15 minutes
        time_saved_seconds=120,
        fuel_saved_liters=0.5,
        co2_avoided_kg=1.2,
        eco_score=85
    )
    
    db_session.add(trip_metrics)
    db_session.commit()
    
    # Verify the metrics were created
    retrieved = db_session.query(TripMetrics).first()
    assert retrieved is not None
    assert retrieved.time_saved_seconds == 120
    assert retrieved.eco_score == 85


def test_model_relationships(db_session):
    """Test relationships between models"""
    # Create user session
    user_session = UserSession(session_id="test_session")
    db_session.add(user_session)
    db_session.commit()
    
    # Create achievement for the user
    achievement = UserAchievement(
        user_session_id=user_session.id,
        achievement_type="eco_warrior",
        points_earned=100,
        milestone_reached="First eco-friendly route"
    )
    db_session.add(achievement)
    db_session.commit()
    
    # Test relationship
    retrieved_user = db_session.query(UserSession).first()
    assert len(retrieved_user.achievements) == 1
    assert retrieved_user.achievements[0].achievement_type == "eco_warrior"