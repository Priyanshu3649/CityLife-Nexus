"""
Air quality and environmental data models
"""
from sqlalchemy import Column, String, Integer, DateTime, Numeric
from .base import BaseModel


class AQIReading(BaseModel):
    __tablename__ = "aqi_readings"
    
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    aqi_value = Column(Integer, nullable=False)
    pm25 = Column(Numeric(6, 2))
    pm10 = Column(Numeric(6, 2))
    no2 = Column(Numeric(6, 2))
    o3 = Column(Numeric(6, 2))
    source = Column(String(50))  # 'openaq', 'government', 'sensor'
    reading_time = Column(DateTime(timezone=True), nullable=False)


class WeatherData(BaseModel):
    __tablename__ = "weather_data"
    
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    temperature_celsius = Column(Numeric(5, 2))
    humidity_percent = Column(Numeric(5, 2))
    wind_speed_kmh = Column(Numeric(5, 2))
    wind_direction = Column(Integer)  # degrees
    precipitation_mm = Column(Numeric(6, 2))
    weather_condition = Column(String(50))  # 'clear', 'rain', 'fog', etc.
    reading_time = Column(DateTime(timezone=True), nullable=False)