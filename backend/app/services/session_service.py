"""
Session management service for SafeAir Navigator
"""
from typing import Optional, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import UserSession, UserAchievement
from app.schemas.user import (
    UserSessionCreate, 
    UserSessionUpdate, 
    UserSessionResponse,
    UserPreferences,
    HealthProfile
)


class SessionService:
    """Service for managing user sessions and preferences"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, session_data: UserSessionCreate) -> UserSessionResponse:
        """Create a new user session"""
        try:
            # Set default preferences if not provided
            default_preferences = {
                "prioritize_time": 0.4,
                "prioritize_air_quality": 0.4,
                "prioritize_safety": 0.2,
                "voice_alerts_enabled": True,
                "gamification_enabled": True,
                "max_detour_minutes": 10
            }
            
            # Set default health profile if not provided
            default_health_profile = {
                "age_group": "adult",
                "respiratory_conditions": [],
                "pollution_sensitivity": 1.0,
                "activity_level": "moderate"
            }
            
            preferences = session_data.preferences.model_dump() if session_data.preferences else default_preferences
            health_profile = session_data.health_profile.model_dump() if session_data.health_profile else default_health_profile
            
            db_session = UserSession(
                session_id=session_data.session_id,
                preferences=preferences,
                health_profile=health_profile,
                vehicle_type=session_data.vehicle_type,
                total_trips=0,
                total_eco_score=0
            )
            
            self.db.add(db_session)
            self.db.commit()
            self.db.refresh(db_session)
            
            return UserSessionResponse.model_validate(db_session)
            
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"Session with ID {session_data.session_id} already exists")
    
    def get_session(self, session_id: str) -> Optional[UserSessionResponse]:
        """Get user session by session ID"""
        db_session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if db_session:
            return UserSessionResponse.model_validate(db_session)
        return None
    
    def update_session(self, session_id: str, update_data: UserSessionUpdate) -> Optional[UserSessionResponse]:
        """Update user session preferences and profile"""
        db_session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if not db_session:
            return None
        
        # Update preferences if provided
        if update_data.preferences:
            current_preferences = db_session.preferences or {}
            current_preferences.update(update_data.preferences.model_dump())
            db_session.preferences = current_preferences
        
        # Update health profile if provided
        if update_data.health_profile:
            current_health_profile = db_session.health_profile or {}
            current_health_profile.update(update_data.health_profile.model_dump())
            db_session.health_profile = current_health_profile
        
        # Update vehicle type if provided
        if update_data.vehicle_type:
            db_session.vehicle_type = update_data.vehicle_type
        
        self.db.commit()
        self.db.refresh(db_session)
        
        return UserSessionResponse.model_validate(db_session)
    
    def increment_trip_count(self, session_id: str) -> bool:
        """Increment the trip count for a session"""
        db_session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if db_session:
            db_session.total_trips += 1
            self.db.commit()
            return True
        return False
    
    def add_eco_score(self, session_id: str, points: int) -> bool:
        """Add eco score points to a session"""
        db_session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if db_session:
            db_session.total_eco_score += points
            self.db.commit()
            return True
        return False
    
    def get_or_create_session(self, session_id: str) -> UserSessionResponse:
        """Get existing session or create a new one with default values"""
        existing_session = self.get_session(session_id)
        if existing_session:
            return existing_session
        
        # Create new session with defaults
        session_data = UserSessionCreate(
            session_id=session_id,
            vehicle_type="car"
        )
        return self.create_session(session_data)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a user session"""
        db_session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if db_session:
            self.db.delete(db_session)
            self.db.commit()
            return True
        return False
    
    def get_session_preferences(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences for a session"""
        db_session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if db_session:
            return db_session.preferences
        return None
    
    def get_session_health_profile(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user health profile for a session"""
        db_session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if db_session:
            return db_session.health_profile
        return None


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"session_{uuid4().hex[:16]}"