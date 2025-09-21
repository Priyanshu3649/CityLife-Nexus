"""
Analytics and metrics Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .base import BaseSchema, CoordinatesSchema, TimestampMixin


class TripMetricsCreate(BaseSchema):
    trip_id: UUID
    user_session_id: UUID
    route_id: UUID
    actual_travel_time: Optional[int] = None
    time_saved_seconds: int = 0
    fuel_saved_liters: float = 0
    co2_avoided_kg: float = 0
    pollution_exposure_avoided: float = 0
    eco_score: int = 0


class TripMetricsResponse(BaseSchema, TimestampMixin):
    id: UUID
    trip_id: UUID
    user_session_id: UUID
    route_id: UUID
    actual_travel_time: Optional[int] = None
    time_saved_seconds: int
    fuel_saved_liters: float
    co2_avoided_kg: float
    pollution_exposure_avoided: float
    eco_score: int
    completed_at: Optional[datetime] = None


class PersonalMetrics(BaseSchema):
    total_trips: int
    total_time_saved_minutes: int
    total_fuel_saved_liters: float
    total_co2_avoided_kg: float
    total_eco_score: int
    average_trip_score: float
    current_streak: int


class CityMetrics(BaseSchema):
    drivers_helped_today: int
    time_saved_hours: int
    fuel_saved_liters: int
    co2_avoided_kg: int
    active_users: int
    total_routes_optimized: int


class ParkingSpaceInfo(BaseSchema):
    location_name: str
    coordinates: CoordinatesSchema
    total_spaces: int
    available_spaces: int
    hourly_rate: Optional[float] = None
    is_ev_charging: bool = False
    walking_distance_meters: Optional[int] = None
    last_updated: datetime


class ChargingStationInfo(BaseSchema):
    station_name: str
    coordinates: CoordinatesSchema
    connector_type: str
    power_kw: int
    available_connectors: int
    total_connectors: int
    pricing_per_kwh: Optional[float] = None
    is_operational: bool = True
    estimated_charging_time_minutes: Optional[int] = None
    last_updated: datetime


class EcoScore(BaseSchema):
    current_score: int
    score_breakdown: dict
    achievements_unlocked: List[str]
    next_milestone: Optional[str] = None
    points_to_next_milestone: Optional[int] = None