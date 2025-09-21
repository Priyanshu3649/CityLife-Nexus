"""
Traffic Light Simulation Service for Delhi NCR
Realistic simulation based on Indian traffic patterns
"""
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import math

from app.schemas.base import CoordinatesSchema
from app.core.config import settings

logger = logging.getLogger(__name__)


class LightColor(Enum):
    """Traffic light colors"""
    RED = "red"
    YELLOW = "yellow" 
    GREEN = "green"


class RoadType(Enum):
    """Road types in Delhi NCR"""
    MAJOR_ARTERIAL = "major_arterial"      # NH-1, Ring Road, Outer Ring Road
    ARTERIAL = "arterial"                  # Main roads like ITO, CP
    COLLECTOR = "collector"                # Sector roads, colony main roads
    LOCAL = "local"                        # Local streets


@dataclass
class TrafficLightState:
    """Current state of a traffic light"""
    light_id: str
    coordinates: CoordinatesSchema
    current_color: LightColor
    time_remaining: int  # seconds
    cycle_duration: int  # total cycle time in seconds
    road_type: RoadType
    intersection_name: str
    last_updated: datetime
    
    # Additional Delhi NCR specific attributes
    is_smart_signal: bool = False
    has_countdown_timer: bool = True
    pedestrian_crossing: bool = True


@dataclass 
class TrafficRecommendation:
    """Speed recommendations for approaching traffic lights"""
    recommended_speed_kmh: float
    action: str  # "maintain", "slow_down", "prepare_to_stop", "go"
    estimated_arrival_color: LightColor
    fuel_efficiency_tip: str
    safety_note: str


class DelhiNCRTrafficLightService:
    """Traffic light simulation service for Delhi NCR region"""
    
    def __init__(self):
        self.traffic_lights: Dict[str, TrafficLightState] = {}
        self.delhi_ncr_bounds = settings.EXTENDED_NCR_BOUNDS
        
        # Delhi-specific traffic patterns
        self.peak_hours = [
            (7, 10),   # Morning peak
            (17, 20),  # Evening peak
            (12, 14)   # Lunch hour (lighter peak)
        ]
        
        # Cycle timings based on Delhi traffic patterns
        self.cycle_timings = {
            RoadType.MAJOR_ARTERIAL: {
                "peak": {"green": 90, "yellow": 4, "red": 120},      # Longer cycles for major roads
                "normal": {"green": 60, "yellow": 3, "red": 90}
            },
            RoadType.ARTERIAL: {
                "peak": {"green": 70, "yellow": 4, "red": 100},
                "normal": {"green": 45, "yellow": 3, "red": 75}
            },
            RoadType.COLLECTOR: {
                "peak": {"green": 50, "yellow": 3, "red": 80},
                "normal": {"green": 35, "yellow": 3, "red": 60}
            },
            RoadType.LOCAL: {
                "peak": {"green": 30, "yellow": 3, "red": 50},
                "normal": {"green": 25, "yellow": 3, "red": 40}
            }
        }
        
        self._initialize_delhi_ncr_signals()
    
    def _initialize_delhi_ncr_signals(self):
        """Initialize traffic signals at major Delhi NCR intersections"""
        
        # Major Delhi intersections with realistic coordinates
        major_intersections = [
            # Central Delhi
            {
                "id": "cp_outer_circle", 
                "name": "Connaught Place Outer Circle",
                "coords": (28.6315, 77.2167), 
                "road_type": RoadType.MAJOR_ARTERIAL,
                "smart": True
            },
            {
                "id": "ito_intersection", 
                "name": "ITO Intersection",
                "coords": (28.6280, 77.2410), 
                "road_type": RoadType.MAJOR_ARTERIAL,
                "smart": True
            },
            {
                "id": "india_gate_circle", 
                "name": "India Gate Circle",
                "coords": (28.6129, 77.2295), 
                "road_type": RoadType.ARTERIAL,
                "smart": False
            },
            
            # South Delhi
            {
                "id": "aiims_intersection", 
                "name": "AIIMS Intersection",
                "coords": (28.5672, 77.2100), 
                "road_type": RoadType.MAJOR_ARTERIAL,
                "smart": True
            },
            {
                "id": "green_park_metro", 
                "name": "Green Park Metro Station",
                "coords": (28.5595, 77.2056), 
                "road_type": RoadType.ARTERIAL,
                "smart": False
            },
            
            # Gurgaon
            {
                "id": "cyber_city_junction", 
                "name": "Cyber City Junction",
                "coords": (28.4950, 77.0890), 
                "road_type": RoadType.MAJOR_ARTERIAL,
                "smart": True
            },
            {
                "id": "udyog_vihar", 
                "name": "Udyog Vihar Phase-1",
                "coords": (28.4817, 77.0873), 
                "road_type": RoadType.ARTERIAL,
                "smart": True
            },
            
            # Noida
            {
                "id": "sector_18_noida", 
                "name": "Sector 18 Noida",
                "coords": (28.5678, 77.3178), 
                "road_type": RoadType.ARTERIAL,
                "smart": True
            },
            {
                "id": "sector_62_noida", 
                "name": "Sector 62 Noida",
                "coords": (28.6074, 77.3714), 
                "road_type": RoadType.COLLECTOR,
                "smart": True
            },
            
            # Ghaziabad
            {
                "id": "raj_nagar_extension", 
                "name": "Raj Nagar Extension",
                "coords": (28.6692, 77.4538), 
                "road_type": RoadType.COLLECTOR,
                "smart": False
            },
            {
                "id": "kaushambi_metro", 
                "name": "Kaushambi Metro Station",
                "coords": (28.6418, 77.3152), 
                "road_type": RoadType.ARTERIAL,
                "smart": True
            }
        ]
        
        # Initialize traffic lights with random initial states
        for intersection in major_intersections:
            coords = CoordinatesSchema(
                latitude=intersection["coords"][0],
                longitude=intersection["coords"][1]
            )
            
            # Random initial state
            colors = list(LightColor)
            initial_color = random.choice(colors)
            
            # Get cycle timing for current time
            is_peak = self._is_peak_hour()
            timing_key = "peak" if is_peak else "normal"
            cycle_times = self.cycle_timings[intersection["road_type"]][timing_key]
            total_cycle = sum(cycle_times.values())
            
            # Random time remaining in current phase
            max_time = max(5, cycle_times[initial_color.value])
            time_remaining = random.randint(5, max_time)
            
            signal = TrafficLightState(
                light_id=intersection["id"],
                coordinates=coords,
                current_color=initial_color,
                time_remaining=time_remaining,
                cycle_duration=total_cycle,
                road_type=intersection["road_type"],
                intersection_name=intersection["name"],
                last_updated=datetime.now(),
                is_smart_signal=intersection["smart"],
                has_countdown_timer=True,
                pedestrian_crossing=True
            )
            
            self.traffic_lights[intersection["id"]] = signal
        
        logger.info(f"Initialized {len(self.traffic_lights)} traffic signals for Delhi NCR")
    
    def _is_peak_hour(self, check_time: Optional[datetime] = None) -> bool:
        """Check if current time is peak hour in Delhi"""
        if check_time is None:
            check_time = datetime.now()
        
        current_hour = check_time.hour
        
        for start_hour, end_hour in self.peak_hours:
            if start_hour <= current_hour <= end_hour:
                return True
        return False
    
    async def get_traffic_signals_near_location(
        self, 
        coordinates: CoordinatesSchema, 
        radius_km: float = 2.0
    ) -> List[TrafficLightState]:
        """Get traffic signals near a given location"""
        
        nearby_signals = []
        
        for signal in self.traffic_lights.values():
            distance = self._calculate_distance(coordinates, signal.coordinates)
            if distance <= radius_km:
                # Update signal state before returning
                await self._update_signal_state(signal)
                nearby_signals.append(signal)
        
        # Sort by distance
        nearby_signals.sort(
            key=lambda s: self._calculate_distance(coordinates, s.coordinates)
        )
        
        return nearby_signals
    
    async def get_traffic_signal_by_id(self, signal_id: str) -> Optional[TrafficLightState]:
        """Get specific traffic signal by ID"""
        if signal_id in self.traffic_lights:
            signal = self.traffic_lights[signal_id]
            await self._update_signal_state(signal)
            return signal
        return None
    
    def _calculate_distance(self, coord1: CoordinatesSchema, coord2: CoordinatesSchema) -> float:
        """Calculate distance between two coordinates in kilometers"""
        lat1, lon1, lat2, lon2 = map(math.radians, [
            coord1.latitude, coord1.longitude,
            coord2.latitude, coord2.longitude
        ])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return c * 6371  # Earth's radius in km
    
    async def _update_signal_state(self, signal: TrafficLightState):
        """Update traffic signal state based on elapsed time"""
        now = datetime.now()
        elapsed_seconds = int((now - signal.last_updated).total_seconds())
        
        if elapsed_seconds <= 0:
            return
        
        # Update time remaining
        signal.time_remaining -= elapsed_seconds
        
        # Check if we need to change phases
        while signal.time_remaining <= 0:
            signal.current_color = self._get_next_color(signal.current_color)
            
            # Get new phase duration
            is_peak = self._is_peak_hour(now)
            timing_key = "peak" if is_peak else "normal"
            cycle_times = self.cycle_timings[signal.road_type][timing_key]
            
            new_duration = cycle_times[signal.current_color.value]
            
            # Add smart signal adaptivity for Delhi
            if signal.is_smart_signal:
                new_duration = self._apply_smart_signal_logic(signal, new_duration, is_peak)
            
            signal.time_remaining += new_duration
        
        signal.last_updated = now
    
    def _get_next_color(self, current_color: LightColor) -> LightColor:
        """Get next traffic light color in sequence"""
        if current_color == LightColor.GREEN:
            return LightColor.YELLOW
        elif current_color == LightColor.YELLOW:
            return LightColor.RED
        else:  # RED
            return LightColor.GREEN
    
    def _apply_smart_signal_logic(
        self, 
        signal: TrafficLightState, 
        base_duration: int, 
        is_peak: bool
    ) -> int:
        """Apply smart signal adaptivity based on Delhi traffic patterns"""
        
        # Smart signals adapt based on traffic conditions
        adaptation_factor = 1.0
        
        # Peak hour adjustments
        if is_peak:
            if signal.road_type == RoadType.MAJOR_ARTERIAL:
                adaptation_factor = 1.3  # Longer green for arterials
            elif signal.current_color == LightColor.GREEN:
                adaptation_factor = 1.2  # Extend green during peak
        
        # Random variation to simulate real-world conditions
        variation = random.uniform(0.9, 1.1)
        
        return int(base_duration * adaptation_factor * variation)


# Global instance
traffic_light_service = DelhiNCRTrafficLightService()