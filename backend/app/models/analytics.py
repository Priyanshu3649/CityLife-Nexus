"""
Analytics and metrics models
"""
from sqlalchemy import Column, String, Integer, Decimal, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class TripMetrics(BaseModel):
    __tablename__ = "trip_metrics"
    
    trip_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    user_session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    actual_travel_time = Column(Integer)  # seconds
    time_saved_seconds = Column(Integer, default=0)
    fuel_saved_liters = Column(Decimal(6, 3), default=0)
    co2_avoided_kg = Column(Decimal(6, 3), default=0)
    pollution_exposure_avoided = Column(Decimal(6, 3), default=0)  # PM2.5 units
    eco_score = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user_session = relationship("UserSession", back_populates="trip_metrics")


class ParkingSpace(BaseModel):
    __tablename__ = "parking_spaces"
    
    location_name = Column(String(100), nullable=False)
    latitude = Column(Decimal(10, 8), nullable=False)
    longitude = Column(Decimal(11, 8), nullable=False)
    total_spaces = Column(Integer, nullable=False)
    available_spaces = Column(Integer, nullable=False)
    hourly_rate = Column(Decimal(5, 2))
    is_ev_charging = Column(Boolean, default=False)
    last_updated = Column(DateTime(timezone=True))


class ChargingStation(BaseModel):
    __tablename__ = "charging_stations"
    
    station_name = Column(String(100), nullable=False)
    latitude = Column(Decimal(10, 8), nullable=False)
    longitude = Column(Decimal(11, 8), nullable=False)
    connector_type = Column(String(20))  # 'CCS', 'CHAdeMO', 'Type2'
    power_kw = Column(Integer)
    available_connectors = Column(Integer, default=0)
    total_connectors = Column(Integer, nullable=False)
    pricing_per_kwh = Column(Decimal(5, 3))
    is_operational = Column(Boolean, default=True)
    last_updated = Column(DateTime(timezone=True))