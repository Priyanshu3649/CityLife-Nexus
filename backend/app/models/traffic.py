"""
Traffic signal and route models
"""
from sqlalchemy import Column, String, Integer, Decimal, Boolean, DateTime, func
from geoalchemy2 import Geometry
from .base import BaseModel


class TrafficSignal(BaseModel):
    __tablename__ = "traffic_signals"
    
    signal_id = Column(String(50), unique=True, nullable=False, index=True)
    location = Column(Geometry('POINT'), nullable=False)
    latitude = Column(Decimal(10, 8), nullable=False)
    longitude = Column(Decimal(11, 8), nullable=False)
    cycle_time_seconds = Column(Integer, nullable=False)
    green_duration = Column(Integer, nullable=False)
    red_duration = Column(Integer, nullable=False)
    yellow_duration = Column(Integer, default=3)
    current_state = Column(String(10))  # 'red', 'green', 'yellow'
    last_state_change = Column(DateTime(timezone=True))
    is_coordinated = Column(Boolean, default=False)
    corridor_id = Column(String(50))


class Route(BaseModel):
    __tablename__ = "routes"
    
    start_lat = Column(Decimal(10, 8), nullable=False)
    start_lng = Column(Decimal(11, 8), nullable=False)
    end_lat = Column(Decimal(10, 8), nullable=False)
    end_lng = Column(Decimal(11, 8), nullable=False)
    start_location = Column(Geometry('POINT'), nullable=False)
    end_location = Column(Geometry('POINT'), nullable=False)
    waypoints = Column(String)  # JSON string of coordinates
    distance_km = Column(Decimal(8, 3), nullable=False)
    estimated_time_minutes = Column(Integer, nullable=False)
    average_aqi = Column(Integer)
    route_score = Column(Decimal(5, 2))
    route_type = Column(String(20), default='optimal')  # 'optimal', 'fast', 'clean', 'safe'