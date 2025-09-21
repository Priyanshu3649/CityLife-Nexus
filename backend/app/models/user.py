"""
User and session models
"""
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class UserSession(BaseModel):
    __tablename__ = "user_sessions"
    
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    preferences = Column(JSON, default={})
    health_profile = Column(JSON, default={})
    vehicle_type = Column(String(20), default="car")
    total_trips = Column(Integer, default=0)
    total_eco_score = Column(Integer, default=0)
    last_active = Column(String)  # Will be updated to DateTime
    
    # Relationships
    trip_metrics = relationship("TripMetrics", back_populates="user_session")
    achievements = relationship("UserAchievement", back_populates="user_session")


class UserAchievement(BaseModel):
    __tablename__ = "user_achievements"
    
    user_session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=False)
    achievement_type = Column(String(50), nullable=False)
    points_earned = Column(Integer, nullable=False)
    milestone_reached = Column(String(100))
    earned_at = Column(String)  # Will be updated to DateTime
    
    # Relationships
    user_session = relationship("UserSession", back_populates="achievements")