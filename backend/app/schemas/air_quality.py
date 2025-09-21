"""
Air quality Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .base import BaseSchema, CoordinatesSchema, TimestampMixin


class AQIReading(BaseSchema):
    coordinates: CoordinatesSchema
    aqi_value: int = Field(ge=0, le=500)
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    source: str
    reading_time: datetime


class AQIRequest(BaseSchema):
    coordinates: CoordinatesSchema
    radius_km: float = Field(default=1.0, ge=0.1, le=50.0)


class RouteAQIData(BaseSchema):
    route_coordinates: list[CoordinatesSchema]
    aqi_readings: list[AQIReading]
    average_aqi: int
    max_aqi: int
    pollution_hotspots: list[CoordinatesSchema]


class HealthImpactEstimate(BaseSchema):
    route_id: Optional[str] = None
    estimated_exposure_pm25: float
    health_risk_score: float = Field(ge=0, le=100)
    recommended_precautions: list[str]
    comparison_to_baseline: float  # percentage difference


class WeatherCondition(BaseSchema):
    coordinates: CoordinatesSchema
    temperature_celsius: float
    humidity_percent: float
    wind_speed_kmh: float
    wind_direction: int = Field(ge=0, le=360)
    precipitation_mm: float
    weather_condition: str
    reading_time: datetime