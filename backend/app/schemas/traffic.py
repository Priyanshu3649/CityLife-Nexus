"""
Traffic prediction schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .base import BaseSchema, CoordinatesSchema


class TrafficSegment(BaseSchema):
    """Represents a segment of a route with traffic data"""
    segment_id: str
    start_coordinates: CoordinatesSchema
    end_coordinates: CoordinatesSchema
    distance_meters: float
    average_speed_kmh: Optional[float] = None
    current_density: Optional[float] = None  # 0.0 to 1.0


class TrafficPrediction(BaseSchema):
    """Traffic prediction for a specific route segment at a future time"""
    segment_index: int
    coordinates: CoordinatesSchema
    eta: datetime
    predicted_density_score: float  # 0.0 to 1.0 (1.0 = heavy congestion)
    confidence_score: float  # 0.0 to 1.0
    factors: Optional[List[str]] = None  # Factors influencing prediction


class RouteTrafficPrediction(BaseSchema):
    """Complete traffic prediction for an entire route"""
    route_id: str
    predictions: List[TrafficPrediction]
    overall_density: float
    peak_density: float
    congested_segments: int
    traffic_assessment: str  # "Light", "Moderate", "Heavy", "Severe"
    estimated_delay_minutes: Optional[float] = None