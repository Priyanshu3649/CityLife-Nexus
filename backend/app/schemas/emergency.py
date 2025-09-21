"""
Emergency and incident Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseSchema, CoordinatesSchema, TimestampMixin


class EmergencyAlertCreate(BaseSchema):
    alert_type: str
    coordinates: CoordinatesSchema
    radius_km: float = Field(ge=0.1, le=50.0)
    severity: int = Field(ge=1, le=5)
    message: str
    created_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class EmergencyAlertResponse(BaseSchema, TimestampMixin):
    id: UUID
    alert_type: str
    coordinates: CoordinatesSchema
    radius_km: float
    severity: int
    message: str
    is_active: bool
    created_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class IncidentReportCreate(BaseSchema):
    reporter_session: str
    coordinates: CoordinatesSchema
    incident_type: str
    description: Optional[str] = None
    severity: int = Field(default=1, ge=1, le=5)


class IncidentReportResponse(BaseSchema, TimestampMixin):
    id: UUID
    reporter_session: str
    coordinates: CoordinatesSchema
    incident_type: str
    description: Optional[str] = None
    severity: int
    verification_count: int
    is_verified: bool


class BroadcastResult(BaseSchema):
    alert_id: UUID
    users_notified: int
    rerouting_triggered: bool
    estimated_impact_radius_km: float