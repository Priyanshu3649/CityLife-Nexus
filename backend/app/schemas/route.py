"""
Route and traffic signal Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from .base import BaseSchema, CoordinatesSchema, TimestampMixin


class RouteRequest(BaseSchema):
    start_coords: CoordinatesSchema
    end_coords: CoordinatesSchema
    preferences: Optional[dict] = None
    avoid_areas: Optional[List[CoordinatesSchema]] = None


class RouteSegment(BaseSchema):
    start_point: CoordinatesSchema
    end_point: CoordinatesSchema
    distance_meters: float
    aqi_level: int
    traffic_signals: List[str]
    estimated_travel_time: int


class RouteOption(BaseSchema):
    id: UUID
    start_coords: CoordinatesSchema
    end_coords: CoordinatesSchema
    waypoints: List[CoordinatesSchema]
    distance_km: float
    estimated_time_minutes: int
    average_aqi: Optional[int] = None
    route_score: Optional[float] = None
    route_type: str
    segments: Optional[List[RouteSegment]] = None


class RouteComparison(BaseSchema):
    fast_route: RouteOption
    clean_route: RouteOption
    balanced_route: Optional[RouteOption] = None
    recommendation: str


class TrafficSignalState(BaseSchema):
    signal_id: str
    coordinates: CoordinatesSchema
    current_state: str  # 'red', 'green', 'yellow'
    cycle_time_seconds: int
    time_to_next_change: Optional[int] = None
    is_coordinated: bool = False


class SignalPrediction(BaseSchema):
    signal_id: str
    predicted_state: str
    confidence: float = Field(ge=0, le=1)
    time_to_arrival: int
    recommended_speed: Optional[float] = None


class GreenWaveCalculation(BaseSchema):
    corridor_id: str
    signals: List[TrafficSignalState]
    optimal_speed_kmh: float
    coordination_offset_seconds: List[int]
    success_probability: float