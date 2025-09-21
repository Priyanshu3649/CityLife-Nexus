"""
Emergency alerts and incident reporting models
"""
from sqlalchemy import Column, String, Integer, Decimal, Boolean, DateTime, Text
from geoalchemy2 import Geometry
from .base import BaseModel


class EmergencyAlert(BaseModel):
    __tablename__ = "emergency_alerts"
    
    alert_type = Column(String(50), nullable=False)  # 'accident', 'pollution_spike', 'fire', 'flood'
    latitude = Column(Decimal(10, 8), nullable=False)
    longitude = Column(Decimal(11, 8), nullable=False)
    radius_km = Column(Decimal(6, 2), nullable=False)
    severity = Column(Integer, nullable=False)  # 1-5 scale
    message = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100))  # system, user_session_id, or authority
    expires_at = Column(DateTime(timezone=True))


class IncidentReport(BaseModel):
    __tablename__ = "incident_reports"
    
    reporter_session = Column(String(100), nullable=False)
    latitude = Column(Decimal(10, 8), nullable=False)
    longitude = Column(Decimal(11, 8), nullable=False)
    incident_type = Column(String(50), nullable=False)  # 'accident', 'road_closure', 'hazard'
    description = Column(Text)
    severity = Column(Integer, default=1)  # 1-5 scale
    verification_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    verification_threshold = Column(Integer, default=3)  # Number of reports needed for verification