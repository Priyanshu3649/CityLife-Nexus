"""
User and session Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime
from .base import BaseSchema, TimestampMixin


class UserPreferences(BaseSchema):
    prioritize_time: float = Field(default=0.4, ge=0, le=1)
    prioritize_air_quality: float = Field(default=0.4, ge=0, le=1)
    prioritize_safety: float = Field(default=0.2, ge=0, le=1)
    voice_alerts_enabled: bool = True
    gamification_enabled: bool = True
    max_detour_minutes: int = Field(default=10, ge=0, le=30)


class HealthProfile(BaseSchema):
    age_group: str = Field(default="adult")  # "child", "adult", "senior"
    respiratory_conditions: List[str] = Field(default_factory=list)
    pollution_sensitivity: float = Field(default=1.0, ge=0.1, le=3.0)
    activity_level: str = Field(default="moderate")  # "low", "moderate", "high"


class UserSessionCreate(BaseSchema):
    session_id: str
    preferences: Optional[UserPreferences] = None
    health_profile: Optional[HealthProfile] = None
    vehicle_type: str = "car"


class UserSessionUpdate(BaseSchema):
    preferences: Optional[UserPreferences] = None
    health_profile: Optional[HealthProfile] = None
    vehicle_type: Optional[str] = None


class UserSessionResponse(BaseSchema, TimestampMixin):
    id: UUID
    session_id: str
    preferences: Dict
    health_profile: Dict
    vehicle_type: str
    total_trips: int
    total_eco_score: int


class UserAchievementCreate(BaseSchema):
    user_session_id: UUID
    achievement_type: str
    points_earned: int
    milestone_reached: Optional[str] = None


class UserAchievementResponse(BaseSchema, TimestampMixin):
    id: UUID
    user_session_id: UUID
    achievement_type: str
    points_earned: int
    milestone_reached: Optional[str] = None
    earned_at: Optional[datetime] = None