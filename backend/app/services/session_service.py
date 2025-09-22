"""
Session management service for CityLife Nexus
"""
from typing import Optional, Dict, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

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
                vehicle_type=session_data.vehicle_type
            )
            
            self.db.add(db_session)
            self.db.commit()
            self.db.refresh(db_session)
            
            return UserSessionResponse.model_validate(db_session)
            
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Session already exists"
            )
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(e)}"
            )
    
    def get_session(self, session_id: str) -> Optional[UserSessionResponse]:
        """Get a user session by ID"""
        try:
            db_session = self.db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if db_session:
                return UserSessionResponse.model_validate(db_session)
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve session: {str(e)}"
            )
    
    def update_session(
        self, 
        session_id: str, 
        session_update: UserSessionUpdate
    ) -> Optional[UserSessionResponse]:
        """Update a user session"""
        try:
            db_session = self.db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if not db_session:
                return None
            
            # Update fields if provided
            update_data = {}
            if session_update.preferences is not None:
                update_data["preferences"] = session_update.preferences.model_dump()
            
            if session_update.health_profile is not None:
                update_data["health_profile"] = session_update.health_profile.model_dump()
            
            if session_update.vehicle_type is not None:
                update_data["vehicle_type"] = session_update.vehicle_type
            
            # Apply updates
            for key, value in update_data.items():
                setattr(db_session, key, value)
            
            self.db.commit()
            self.db.refresh(db_session)
            
            return UserSessionResponse.model_validate(db_session)
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update session: {str(e)}"
            )
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a user session"""
        try:
            db_session = self.db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if not db_session:
                return False
            
            self.db.delete(db_session)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete session: {str(e)}"
            )