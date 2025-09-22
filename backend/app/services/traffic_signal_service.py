"""
Traffic Signal Service with mock data for demonstration
"""
import asyncio
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import math
import logging

from app.schemas.base import CoordinatesSchema
from app.schemas.route import TrafficSignalState, SignalPrediction, GreenWaveCalculation
from app.models.traffic import TrafficSignal as TrafficSignalModel
from app.services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


class TrafficSignalService:
    """Service for traffic signal management and prediction"""
    
    def __init__(self):
        # Signal timing patterns for different road types
        self.signal_patterns = {
            "major_arterial": {"cycle": 120, "green": 60, "yellow": 4, "red": 56},
            "minor_arterial": {"cycle": 90, "green": 45, "yellow": 3, "red": 42},
            "collector": {"cycle": 60, "green": 30, "yellow": 3, "red": 27},
            "local": {"cycle": 45, "green": 20, "yellow": 3, "red": 22}
        }
        
        # Coordination corridors for green wave optimization
        self.corridors = {
            "corridor_1": ["TL001", "TL002", "TL003", "TL004"],
            "corridor_2": ["TL005", "TL006", "TL007"],
            "corridor_3": ["TL008", "TL009", "TL010", "TL011", "TL012"]
        }
        
        # Mock traffic signals database - in production this would be real infrastructure
        self.mock_signals = self._initialize_mock_signals()
    
    def _initialize_mock_signals(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mock traffic signals for demonstration"""
        signals = {}
        
        # Delhi area signals (around Connaught Place)
        signal_locations = [
            {"id": "TL001", "lat": 28.6304, "lng": 77.2177, "type": "major_arterial"},
            {"id": "TL002", "lat": 28.6289, "lng": 77.2156, "type": "major_arterial"},
            {"id": "TL003", "lat": 28.6274, "lng": 77.2135, "type": "major_arterial"},
            {"id": "TL004", "lat": 28.6259, "lng": 77.2114, "type": "major_arterial"},
            {"id": "TL005", "lat": 28.6320, "lng": 77.2200, "type": "minor_arterial"},
            {"id": "TL006", "lat": 28.6310, "lng": 77.2220, "type": "minor_arterial"},
            {"id": "TL007", "lat": 28.6300, "lng": 77.2240, "type": "minor_arterial"},
            {"id": "TL008", "lat": 28.6250, "lng": 77.2080, "type": "collector"},
            {"id": "TL009", "lat": 28.6240, "lng": 77.2060, "type": "collector"},
            {"id": "TL010", "lat": 28.6230, "lng": 77.2040, "type": "collector"},
            {"id": "TL011", "lat": 28.6220, "lng": 77.2020, "type": "collector"},
            {"id": "TL012", "lat": 28.6210, "lng": 77.2000, "type": "collector"},
            {"id": "TL013", "lat": 28.6350, "lng": 77.2250, "type": "local"},
            {"id": "TL014", "lat": 28.6180, "lng": 77.1980, "type": "local"},
            {"id": "TL015", "lat": 28.6400, "lng": 77.2300, "type": "local"},
            # Christ University Ghaziabad area signals
            {"id": "CU001", "lat": 28.6837, "lng": 77.4104, "type": "major_arterial", "name": "Christ University Main Gate"},
            {"id": "CU002", "lat": 28.6850, "lng": 77.4120, "type": "minor_arterial", "name": "Mariam Nagar Crossroads"},
            {"id": "CU003", "lat": 28.6825, "lng": 77.4090, "type": "collector", "name": "Nandgram Road Junction"},
            {"id": "CU004", "lat": 28.6860, "lng": 77.4135, "type": "local", "name": "Meerut Road Signal"},
            {"id": "CU005", "lat": 28.6810, "lng": 77.4075, "type": "collector", "name": "Sewa Nagar Intersection"}
        ]
        
        for signal_info in signal_locations:
            pattern = self.signal_patterns[signal_info["type"]]
            
            # Random offset for signal start time (0-cycle_time seconds)
            offset = random.randint(0, pattern["cycle"])
            
            signals[signal_info["id"]] = {
                "signal_id": signal_info["id"],
                "coordinates": CoordinatesSchema(
                    latitude=signal_info["lat"],
                    longitude=signal_info["lng"]
                ),
                "road_type": signal_info["type"],
                "cycle_time_seconds": pattern["cycle"],
                "green_duration": pattern["green"],
                "yellow_duration": pattern["yellow"],
                "red_duration": pattern["red"],
                "offset_seconds": offset,
                "is_coordinated": signal_info["id"] in [
                    signal for corridor in self.corridors.values() for signal in corridor
                ],
                "corridor_id": self._get_corridor_id(signal_info["id"]),
                "last_updated": datetime.utcnow(),
                "adaptive": random.choice([True, False]),  # Some signals are adaptive
                "pedestrian_crossing": random.choice([True, False]),
                "intersection_name": signal_info.get("name", signal_info["id"])  # Add intersection name
            }
        
        return signals
    
    def _get_corridor_id(self, signal_id: str) -> Optional[str]:
        """Get corridor ID for a signal"""
        for corridor_id, signals in self.corridors.items():
            if signal_id in signals:
                return corridor_id
        return None
    
    def get_current_signal_state(self, signal_id: str) -> Optional[TrafficSignalState]:
        """Get current state of a traffic signal"""
        if signal_id not in self.mock_signals:
            return None
        
        signal_data = self.mock_signals[signal_id]
        current_time = datetime.utcnow()
        
        # Calculate current state based on cycle timing
        cycle_start = signal_data["last_updated"]
        elapsed_seconds = (current_time - cycle_start).total_seconds()
        
        # Account for signal offset
        cycle_position = (elapsed_seconds + signal_data["offset_seconds"]) % signal_data["cycle_time_seconds"]
        
        # Determine current state
        green_duration = signal_data["green_duration"]
        yellow_duration = signal_data["yellow_duration"]
        
        if cycle_position < green_duration:
            current_state = "green"
            time_to_next_change = green_duration - cycle_position
        elif cycle_position < green_duration + yellow_duration:
            current_state = "yellow"
            time_to_next_change = (green_duration + yellow_duration) - cycle_position
        else:
            current_state = "red"
            time_to_next_change = signal_data["cycle_time_seconds"] - cycle_position
        
        # Generate recommendation based on current state
        recommendation = self._generate_recommendation(
            current_state, 
            int(time_to_next_change), 
            signal_data.get("intersection_name", signal_id)
        )
        
        return TrafficSignalState(
            signal_id=signal_id,
            coordinates=signal_data["coordinates"],
            current_state=current_state,
            cycle_time_seconds=signal_data["cycle_time_seconds"],
            time_to_next_change=int(time_to_next_change),
            is_coordinated=signal_data["is_coordinated"],
            intersection_name=signal_data.get("intersection_name"),
            recommendation=recommendation
        )
    
    def _generate_recommendation(
        self, 
        current_state: str, 
        time_to_next_change: int, 
        intersection_name: str
    ) -> str:
        """Generate recommendation based on signal state"""
        if current_state == "green":
            if time_to_next_change > 10:
                return f"Proceed through {intersection_name} - Green light for {time_to_next_change}s"
            else:
                return f"Proceed quickly through {intersection_name} - Green light changing soon"
        elif current_state == "yellow":
            return f"Prepare to stop at {intersection_name} - Yellow light for {time_to_next_change}s"
        else:  # red
            if time_to_next_change > 30:
                return f"Stop at {intersection_name} - Red light for {time_to_next_change}s"
            else:
                return f"Prepare for green at {intersection_name} - Red light changing soon"
    
    def predict_signal_state(
        self,
        signal_id: str,
        arrival_time: datetime,
        current_speed_kmh: float
    ) -> Optional[SignalPrediction]:
        """Predict signal state when vehicle arrives"""
        if signal_id not in self.mock_signals:
            return None
        
        signal_data = self.mock_signals[signal_id]
        
        # Calculate time until arrival
        time_to_arrival = (arrival_time - datetime.utcnow()).total_seconds()
        
        if time_to_arrival < 0:
            time_to_arrival = 0
        
        # Calculate signal state at arrival time
        cycle_start = signal_data["last_updated"]
        elapsed_at_arrival = (arrival_time - cycle_start).total_seconds()
        cycle_position = (elapsed_at_arrival + signal_data["offset_seconds"]) % signal_data["cycle_time_seconds"]
        
        green_duration = signal_data["green_duration"]
        yellow_duration = signal_data["yellow_duration"]
        
        if cycle_position < green_duration:
            predicted_state = "green"
            confidence = 0.9
        elif cycle_position < green_duration + yellow_duration:
            predicted_state = "yellow"
            confidence = 0.8
        else:
            predicted_state = "red"
            confidence = 0.9
        
        # Calculate recommended speed to catch green light
        recommended_speed = self._calculate_recommended_speed(
            signal_data, time_to_arrival, current_speed_kmh
        )
        
        return SignalPrediction(
            signal_id=signal_id,
            predicted_state=predicted_state,
            confidence=confidence,
            time_to_arrival=int(time_to_arrival),
            recommended_speed=recommended_speed
        )
    
    def _calculate_recommended_speed(
        self,
        signal_data: Dict[str, Any],
        time_to_arrival: float,
        current_speed_kmh: float
    ) -> Optional[float]:
        """Calculate recommended speed to catch green light"""
        if time_to_arrival <= 0:
            return None
        
        cycle_time = signal_data["cycle_time_seconds"]
        green_duration = signal_data["green_duration"]
        
        # Find next green phase
        current_time = datetime.utcnow()
        cycle_start = signal_data["last_updated"]
        elapsed = (current_time - cycle_start).total_seconds()
        cycle_position = (elapsed + signal_data["offset_seconds"]) % cycle_time
        
        # Time until next green phase starts
        if cycle_position < green_duration:
            # Currently green, next green is one full cycle away
            time_to_next_green = cycle_time - cycle_position
        else:
            # Currently red/yellow, calculate time to next green
            time_to_next_green = cycle_time - cycle_position
        
        # If we can make it to the current or next green phase
        if time_to_arrival <= time_to_next_green + green_duration:
            # Recommend maintaining current speed or slight adjustment
            speed_adjustment = random.uniform(-5, 5)  # ±5 km/h adjustment
            recommended = max(20, min(60, current_speed_kmh + speed_adjustment))
            return round(recommended, 1)
        
        return None
    
    def get_signals_near_location(
        self,
        coordinates: CoordinatesSchema,
        radius_km: float = 2.0
    ) -> List[TrafficSignalState]:
        """Get all traffic signals near a location"""
        nearby_signals = []
        
        for signal_id, signal_data in self.mock_signals.items():
            distance = self._calculate_distance(
                coordinates,
                signal_data["coordinates"]
            )
            
            if distance <= radius_km:
                signal_state = self.get_current_signal_state(signal_id)
                if signal_state:
                    nearby_signals.append(signal_state)
        
        return nearby_signals
    
    def get_signals_along_route(
        self,
        route_coordinates: List[CoordinatesSchema],
        buffer_meters: float = 100.0
    ) -> List[TrafficSignalState]:
        """Get traffic signals along a route"""
        route_signals = []
        
        for signal_id, signal_data in self.mock_signals.items():
            signal_coords = signal_data["coordinates"]
            
            # Check if signal is near any point on the route
            for route_point in route_coordinates:
                distance_km = self._calculate_distance(route_point, signal_coords)
                
                if distance_km <= (buffer_meters / 1000.0):
                    signal_state = self.get_current_signal_state(signal_id)
                    if signal_state and signal_state not in route_signals:
                        route_signals.append(signal_state)
                    break
        
        return route_signals
    
    def calculate_green_wave_timing(
        self,
        corridor_id: str,
        average_speed_kmh: float = 50.0
    ) -> Optional[GreenWaveCalculation]:
        """Calculate optimal green wave timing for a corridor"""
        if corridor_id not in self.corridors:
            return None
        
        signal_ids = self.corridors[corridor_id]
        signals = []
        
        # Get signal states for the corridor
        for signal_id in signal_ids:
            signal_state = self.get_current_signal_state(signal_id)
            if signal_state:
                signals.append(signal_state)
        
        if len(signals) < 2:
            return None
        
        # Calculate distances between consecutive signals
        distances = []
        for i in range(len(signals) - 1):
            distance = self._calculate_distance(
                signals[i].coordinates,
                signals[i + 1].coordinates
            ) * 1000  # Convert to meters
            distances.append(distance)
        
        # Calculate optimal offsets
        speed_ms = average_speed_kmh / 3.6  # Convert km/h to m/s
        offsets = []
        cumulative_offset = 0
        
        for distance in distances:
            travel_time = distance / speed_ms
            cumulative_offset += travel_time
            offsets.append(int(cumulative_offset))
        
        # Calculate success probability based on signal coordination
        coordination_factor = 0.8 if all(s.is_coordinated for s in signals) else 0.6
        traffic_factor = min(1.0, 60.0 / average_speed_kmh)  # Lower speed = lower success
        success_probability = coordination_factor * traffic_factor
        
        return GreenWaveCalculation(
            corridor_id=corridor_id,
            signals=signals,
            optimal_speed_kmh=average_speed_kmh,
            coordination_offset_seconds=offsets,
            success_probability=round(success_probability, 2)
        )
    
    def optimize_corridor_timing(
        self,
        signal_chain: List[str],
        traffic_density: str = "moderate"
    ) -> Dict[str, Any]:
        """Optimize timing for a chain of signals"""
        if len(signal_chain) < 2:
            return {"error": "At least 2 signals required for optimization"}
        
        # Get signal data
        signals_data = []
        for signal_id in signal_chain:
            if signal_id in self.mock_signals:
                signals_data.append(self.mock_signals[signal_id])
        
        if len(signals_data) < 2:
            return {"error": "Invalid signal IDs provided"}
        
        # Calculate optimal speed based on traffic density
        speed_map = {
            "light": 55.0,
            "moderate": 45.0,
            "heavy": 35.0
        }
        optimal_speed = speed_map.get(traffic_density, 45.0)
        
        # Calculate green wave parameters
        total_distance = 0
        travel_times = []
        
        for i in range(len(signals_data) - 1):
            distance = self._calculate_distance(
                signals_data[i]["coordinates"],
                signals_data[i + 1]["coordinates"]
            ) * 1000  # Convert to meters
            
            travel_time = distance / (optimal_speed / 3.6)  # Convert speed to m/s
            travel_times.append(travel_time)
            total_distance += distance
        
        # Calculate coordination efficiency
        avg_cycle_time = sum(s["cycle_time_seconds"] for s in signals_data) / len(signals_data)
        coordination_efficiency = min(0.95, 0.6 + (0.35 * (optimal_speed / 60.0)))
        
        return {
            "signal_chain": signal_chain,
            "optimal_speed_kmh": optimal_speed,
            "total_distance_meters": total_distance,
            "estimated_travel_time_seconds": sum(travel_times),
            "coordination_efficiency": round(coordination_efficiency, 2),
            "average_cycle_time": avg_cycle_time,
            "recommended_offsets": [int(sum(travel_times[:i+1])) for i in range(len(travel_times))],
            "traffic_density": traffic_density
        }
    
    def simulate_adaptive_timing(
        self,
        signal_id: str,
        traffic_volume: int,
        pedestrian_count: int = 0
    ) -> Dict[str, Any]:
        """Simulate adaptive signal timing based on traffic conditions"""
        if signal_id not in self.mock_signals:
            return {"error": "Signal not found"}
        
        signal_data = self.mock_signals[signal_id]
        base_green = signal_data["green_duration"]
        base_cycle = signal_data["cycle_time_seconds"]
        
        # Adjust timing based on traffic volume
        if traffic_volume > 100:  # Heavy traffic
            green_extension = min(20, traffic_volume // 10)
            new_green = base_green + green_extension
        elif traffic_volume < 30:  # Light traffic
            green_reduction = min(10, (30 - traffic_volume) // 3)
            new_green = max(15, base_green - green_reduction)
        else:  # Moderate traffic
            new_green = base_green
        
        # Adjust for pedestrian crossings
        if signal_data["pedestrian_crossing"] and pedestrian_count > 5:
            pedestrian_time = min(15, pedestrian_count // 2)
            new_green += pedestrian_time
        
        # Calculate new cycle time
        new_cycle = new_green + signal_data["yellow_duration"] + signal_data["red_duration"]
        
        # Update signal timing (in real system, this would update hardware)
        efficiency_gain = abs(base_cycle - new_cycle) / base_cycle
        
        return {
            "signal_id": signal_id,
            "original_timing": {
                "green": base_green,
                "cycle": base_cycle
            },
            "adaptive_timing": {
                "green": new_green,
                "cycle": new_cycle
            },
            "traffic_volume": traffic_volume,
            "pedestrian_count": pedestrian_count,
            "efficiency_gain_percent": round(efficiency_gain * 100, 1),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_distance(
        self,
        coord1: CoordinatesSchema,
        coord2: CoordinatesSchema
    ) -> float:
        """Calculate distance between two coordinates in kilometers"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [
            coord1.latitude, coord1.longitude,
            coord2.latitude, coord2.longitude
        ])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    async def store_signal_data(self, db: Session):
        """Store mock signal data in database for persistence"""
        try:
            for signal_id, signal_data in self.mock_signals.items():
                # Check if signal already exists
                existing = db.query(TrafficSignalModel).filter(
                    TrafficSignalModel.signal_id == signal_id
                ).first()
                
                if not existing:
                    db_signal = TrafficSignalModel(
                        signal_id=signal_id,
                        latitude=signal_data["coordinates"].latitude,
                        longitude=signal_data["coordinates"].longitude,
                        cycle_time_seconds=signal_data["cycle_time_seconds"],
                        green_duration=signal_data["green_duration"],
                        red_duration=signal_data["red_duration"],
                        yellow_duration=signal_data["yellow_duration"],
                        is_coordinated=signal_data["is_coordinated"],
                        corridor_id=signal_data["corridor_id"]
                    )
                    
                    db.add(db_signal)
            
            db.commit()
            logger.info(f"Stored {len(self.mock_signals)} traffic signals in database")
            
        except Exception as e:
            logger.error(f"Failed to store signal data: {e}")
            db.rollback()
    
    def get_corridor_performance(self, corridor_id: str) -> Dict[str, Any]:
        """Get performance metrics for a corridor"""
        if corridor_id not in self.corridors:
            return {"error": "Corridor not found"}
        
        signal_ids = self.corridors[corridor_id]
        signals = [self.get_current_signal_state(sid) for sid in signal_ids if sid in self.mock_signals]
        
        # Filter out None values
        signals = [s for s in signals if s is not None]
        
        if not signals:
            return {"error": "No signals found in corridor"}
        
        # Calculate performance metrics
        coordinated_count = sum(1 for s in signals if s.is_coordinated)
        coordination_percentage = (coordinated_count / len(signals)) * 100
        
        # Simulate performance data
        avg_delay = random.uniform(15, 45)  # seconds
        throughput = random.randint(800, 1200)  # vehicles per hour
        fuel_savings = random.uniform(10, 25)  # percentage
        
        return {
            "corridor_id": corridor_id,
            "total_signals": len(signals),
            "coordinated_signals": coordinated_count,
            "coordination_percentage": round(coordination_percentage, 1),
            "average_delay_seconds": round(avg_delay, 1),
            "throughput_vehicles_per_hour": throughput,
            "estimated_fuel_savings_percent": round(fuel_savings, 1),
            "last_updated": datetime.utcnow().isoformat()
        }


# Global instance
traffic_signal_service = TrafficSignalService()