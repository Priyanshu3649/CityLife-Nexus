"""
Green Wave Synchronization Service
Advanced traffic signal coordination for optimal flow
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.schemas.base import CoordinatesSchema
from app.schemas.route import TrafficSignalState, GreenWaveCalculation
from app.services.traffic_signal_service import traffic_signal_service

logger = logging.getLogger(__name__)


class GreenWaveService:
    """Advanced green wave synchronization and optimization"""
    
    def __init__(self):
        # Green wave parameters
        self.optimal_speed_range = (40, 60)  # km/h
        self.max_coordination_distance = 5.0  # km
        self.min_signals_for_wave = 2
        
        # Traffic flow models
        self.flow_models = {
            "urban": {"base_speed": 45, "capacity": 1800, "saturation_flow": 1900},
            "arterial": {"base_speed": 55, "capacity": 2000, "saturation_flow": 2100},
            "highway": {"base_speed": 65, "capacity": 2200, "saturation_flow": 2300}
        }
    
    def calculate_green_wave_offset(
        self,
        distance_meters: float,
        average_speed_kmh: float,
        signal_cycle_time: int = 120
    ) -> int:
        """
        Calculate optimal signal offset for green wave coordination
        
        Args:
            distance_meters: Distance between two traffic signals
            average_speed_kmh: Average vehicle speed on this road
            signal_cycle_time: Signal cycle time in seconds
            
        Returns:
            offset_seconds: Time delay for downstream signal
        """
        try:
            # Convert speed to m/s
            speed_ms = average_speed_kmh / 3.6
            
            # Calculate travel time between signals
            travel_time = distance_meters / speed_ms
            
            # Calculate offset as percentage of cycle time
            offset_seconds = travel_time % signal_cycle_time
            
            return int(offset_seconds)
            
        except Exception as e:
            logger.error(f"Green wave offset calculation failed: {e}")
            return 0
    
    def optimize_corridor_timing(
        self,
        signal_chain: List[str],
        target_speed_kmh: float = 50.0,
        traffic_density: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Optimize timing for entire corridor of signals
        
        Args:
            signal_chain: List of signal IDs in sequence
            target_speed_kmh: Desired travel speed
            traffic_density: Current traffic conditions
            
        Returns:
            Optimization results with timing recommendations
        """
        try:
            if len(signal_chain) < self.min_signals_for_wave:
                return {
                    "error": f"Minimum {self.min_signals_for_wave} signals required for green wave"
                }
            
            # Get signal data
            signals_data = []
            for signal_id in signal_chain:
                signal_state = traffic_signal_service.get_current_signal_state(signal_id)
                if signal_state:
                    signals_data.append({
                        "signal_id": signal_id,
                        "state": signal_state,
                        "coordinates": signal_state.coordinates
                    })
            
            if len(signals_data) < self.min_signals_for_wave:
                return {"error": "Insufficient valid signals found"}
            
            # Calculate distances between consecutive signals
            distances = []
            for i in range(len(signals_data) - 1):
                distance = self._calculate_distance(
                    signals_data[i]["coordinates"],
                    signals_data[i + 1]["coordinates"]
                ) * 1000  # Convert to meters
                distances.append(distance)
            
            # Optimize speed based on traffic density
            optimized_speed = self._optimize_speed_for_conditions(
                target_speed_kmh, traffic_density, distances
            )
            
            # Calculate optimal offsets
            offsets = []
            cumulative_time = 0
            
            for i, distance in enumerate(distances):
                travel_time = distance / (optimized_speed / 3.6)  # Convert speed to m/s
                cumulative_time += travel_time
                
                # Get cycle time for this signal
                cycle_time = signals_data[i + 1]["state"].cycle_time_seconds
                
                # Calculate offset within cycle
                offset = int(cumulative_time % cycle_time)
                offsets.append(offset)
            
            # Calculate coordination efficiency
            efficiency = self._calculate_coordination_efficiency(
                signals_data, distances, optimized_speed
            )
            
            # Estimate performance improvements
            performance_gains = self._estimate_performance_gains(
                len(signals_data), sum(distances), efficiency
            )
            
            return {
                "corridor_id": f"corridor_{signal_chain[0]}_{signal_chain[-1]}",
                "signal_chain": signal_chain,
                "total_signals": len(signals_data),
                "total_distance_meters": sum(distances),
                "optimized_speed_kmh": round(optimized_speed, 1),
                "recommended_offsets": offsets,
                "coordination_efficiency": round(efficiency, 2),
                "estimated_travel_time_seconds": int(sum(distances) / (optimized_speed / 3.6)),
                "performance_gains": performance_gains,
                "traffic_density": traffic_density,
                "optimization_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Corridor optimization failed: {e}")
            return {"error": str(e)}
    
    def simulate_green_wave_progression(
        self,
        corridor_id: str,
        vehicle_speed_kmh: float,
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        Simulate vehicle progression through green wave
        
        Args:
            corridor_id: ID of the corridor to simulate
            vehicle_speed_kmh: Vehicle travel speed
            start_time: Simulation start time
            
        Returns:
            Simulation results with signal encounters
        """
        try:
            # Get corridor signals
            if corridor_id not in traffic_signal_service.corridors:
                return {"error": "Corridor not found"}
            
            signal_ids = traffic_signal_service.corridors[corridor_id]
            
            # Get signal states and positions
            signals = []
            for signal_id in signal_ids:
                signal_state = traffic_signal_service.get_current_signal_state(signal_id)
                if signal_state:
                    signals.append(signal_state)
            
            if len(signals) < 2:
                return {"error": "Insufficient signals for simulation"}
            
            # Calculate distances between signals
            distances = []
            for i in range(len(signals) - 1):
                distance = self._calculate_distance(
                    signals[i].coordinates,
                    signals[i + 1].coordinates
                ) * 1000  # Convert to meters
                distances.append(distance)
            
            # Simulate vehicle progression
            simulation_results = []
            current_time = start_time
            cumulative_distance = 0
            
            for i, signal in enumerate(signals):
                # Calculate arrival time at this signal
                if i > 0:
                    travel_time = distances[i - 1] / (vehicle_speed_kmh / 3.6)
                    current_time += timedelta(seconds=travel_time)
                    cumulative_distance += distances[i - 1]
                
                # Predict signal state at arrival
                prediction = traffic_signal_service.predict_signal_state(
                    signal_id=signal.signal_id,
                    arrival_time=current_time,
                    current_speed_kmh=vehicle_speed_kmh
                )
                
                encounter = {
                    "signal_id": signal.signal_id,
                    "arrival_time": current_time.isoformat(),
                    "cumulative_distance_meters": int(cumulative_distance),
                    "predicted_state": prediction.predicted_state if prediction else "unknown",
                    "confidence": prediction.confidence if prediction else 0.0,
                    "recommended_speed": prediction.recommended_speed if prediction else None,
                    "stop_required": prediction.predicted_state == "red" if prediction else True
                }
                
                simulation_results.append(encounter)
            
            # Calculate overall performance
            stops_required = sum(1 for r in simulation_results if r["stop_required"])
            green_hits = sum(1 for r in simulation_results if r["predicted_state"] == "green")
            
            performance = {
                "total_signals": len(signals),
                "green_hits": green_hits,
                "stops_required": stops_required,
                "green_wave_efficiency": round((green_hits / len(signals)) * 100, 1),
                "total_travel_time_seconds": int((current_time - start_time).total_seconds()),
                "average_speed_maintained": vehicle_speed_kmh
            }
            
            return {
                "corridor_id": corridor_id,
                "simulation_speed_kmh": vehicle_speed_kmh,
                "start_time": start_time.isoformat(),
                "signal_encounters": simulation_results,
                "performance_summary": performance
            }
            
        except Exception as e:
            logger.error(f"Green wave simulation failed: {e}")
            return {"error": str(e)}
    
    def calculate_bandwidth_efficiency(
        self,
        signal_chain: List[str],
        speed_range: Tuple[float, float] = (40, 60)
    ) -> Dict[str, Any]:
        """
        Calculate green wave bandwidth efficiency
        
        Args:
            signal_chain: List of signal IDs
            speed_range: Min and max speeds to analyze
            
        Returns:
            Bandwidth analysis results
        """
        try:
            # Get signal data
            signals_data = []
            for signal_id in signal_chain:
                signal_state = traffic_signal_service.get_current_signal_state(signal_id)
                if signal_state:
                    signals_data.append(signal_state)
            
            if len(signals_data) < 2:
                return {"error": "Insufficient signals for bandwidth analysis"}
            
            # Calculate distances
            distances = []
            for i in range(len(signals_data) - 1):
                distance = self._calculate_distance(
                    signals_data[i].coordinates,
                    signals_data[i + 1].coordinates
                ) * 1000
                distances.append(distance)
            
            # Analyze bandwidth for different speeds
            speed_analysis = []
            min_speed, max_speed = speed_range
            
            for speed in range(int(min_speed), int(max_speed) + 5, 5):
                bandwidth = self._calculate_bandwidth_for_speed(
                    signals_data, distances, speed
                )
                
                speed_analysis.append({
                    "speed_kmh": speed,
                    "bandwidth_seconds": bandwidth,
                    "efficiency_percent": min(100, (bandwidth / 60) * 100)  # Normalize to 60s max
                })
            
            # Find optimal speed
            optimal_analysis = max(speed_analysis, key=lambda x: x["efficiency_percent"])
            
            # Calculate overall corridor metrics
            total_distance = sum(distances)
            avg_cycle_time = sum(s.cycle_time_seconds for s in signals_data) / len(signals_data)
            
            return {
                "signal_chain": signal_chain,
                "total_distance_meters": total_distance,
                "average_cycle_time": avg_cycle_time,
                "speed_analysis": speed_analysis,
                "optimal_speed": optimal_analysis,
                "coordination_potential": self._assess_coordination_potential(signals_data),
                "recommendations": self._generate_bandwidth_recommendations(
                    optimal_analysis, signals_data
                )
            }
            
        except Exception as e:
            logger.error(f"Bandwidth efficiency calculation failed: {e}")
            return {"error": str(e)}
    
    def _optimize_speed_for_conditions(
        self,
        target_speed: float,
        traffic_density: str,
        distances: List[float]
    ) -> float:
        """Optimize speed based on traffic conditions"""
        # Base speed adjustments for traffic density
        density_factors = {
            "light": 1.1,    # Can go slightly faster
            "moderate": 1.0,  # Target speed
            "heavy": 0.85    # Must go slower
        }
        
        factor = density_factors.get(traffic_density, 1.0)
        adjusted_speed = target_speed * factor
        
        # Consider distance-based adjustments
        avg_distance = sum(distances) / len(distances) if distances else 1000
        
        if avg_distance < 300:  # Short blocks
            adjusted_speed *= 0.9
        elif avg_distance > 800:  # Long blocks
            adjusted_speed *= 1.05
        
        # Ensure speed stays within reasonable bounds
        return max(25, min(70, adjusted_speed))
    
    def _calculate_coordination_efficiency(
        self,
        signals_data: List[Dict],
        distances: List[float],
        speed_kmh: float
    ) -> float:
        """Calculate coordination efficiency score"""
        try:
            # Base efficiency from signal coordination
            coordinated_count = sum(
                1 for s in signals_data 
                if s["state"].is_coordinated
            )
            coordination_ratio = coordinated_count / len(signals_data)
            
            # Distance-based efficiency
            avg_distance = sum(distances) / len(distances)
            distance_factor = min(1.0, avg_distance / 500)  # Optimal around 500m
            
            # Speed consistency factor
            speed_factor = 1.0
            if 45 <= speed_kmh <= 55:
                speed_factor = 1.0
            else:
                speed_factor = max(0.7, 1.0 - abs(speed_kmh - 50) * 0.01)
            
            # Cycle time consistency
            cycle_times = [s["state"].cycle_time_seconds for s in signals_data]
            cycle_variance = max(cycle_times) - min(cycle_times)
            cycle_factor = max(0.8, 1.0 - cycle_variance / 60)
            
            # Combined efficiency
            efficiency = (
                coordination_ratio * 0.4 +
                distance_factor * 0.2 +
                speed_factor * 0.2 +
                cycle_factor * 0.2
            )
            
            return min(1.0, efficiency)
            
        except Exception as e:
            logger.error(f"Efficiency calculation failed: {e}")
            return 0.5
    
    def _estimate_performance_gains(
        self,
        signal_count: int,
        total_distance: float,
        efficiency: float
    ) -> Dict[str, Any]:
        """Estimate performance improvements from coordination"""
        try:
            # Base improvements scale with efficiency and signal count
            base_improvement = efficiency * (signal_count / 10)  # More signals = more potential
            
            # Time savings (percentage)
            time_savings_percent = min(30, base_improvement * 25)
            
            # Fuel savings (percentage)
            fuel_savings_percent = min(20, base_improvement * 20)
            
            # Emission reductions
            co2_reduction_percent = fuel_savings_percent * 0.9
            
            # Stop reduction
            stops_reduced = min(signal_count - 1, int(efficiency * signal_count * 0.7))
            
            # Calculate absolute values for typical trip
            typical_trip_time = (total_distance / 1000) / 45 * 60  # minutes at 45 km/h
            time_saved_minutes = typical_trip_time * (time_savings_percent / 100)
            
            return {
                "time_savings_percent": round(time_savings_percent, 1),
                "fuel_savings_percent": round(fuel_savings_percent, 1),
                "co2_reduction_percent": round(co2_reduction_percent, 1),
                "stops_reduced": stops_reduced,
                "estimated_time_saved_minutes": round(time_saved_minutes, 1),
                "efficiency_score": round(efficiency * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Performance estimation failed: {e}")
            return {}
    
    def _calculate_bandwidth_for_speed(
        self,
        signals_data: List,
        distances: List[float],
        speed_kmh: float
    ) -> float:
        """Calculate green bandwidth for specific speed"""
        try:
            # Calculate travel times between signals
            travel_times = [
                distance / (speed_kmh / 3.6) 
                for distance in distances
            ]
            
            # Find minimum green time across all signals
            min_green_time = min(
                signal.cycle_time_seconds * 0.4  # Assume 40% green time
                for signal in signals_data
            )
            
            # Calculate bandwidth based on travel time synchronization
            max_travel_time = max(travel_times) if travel_times else 0
            
            # Bandwidth is limited by shortest green phase and travel time sync
            bandwidth = min(min_green_time, max_travel_time * 0.8)
            
            return max(0, bandwidth)
            
        except Exception as e:
            logger.error(f"Bandwidth calculation failed: {e}")
            return 0
    
    def _assess_coordination_potential(self, signals_data: List) -> Dict[str, Any]:
        """Assess potential for signal coordination"""
        try:
            # Check cycle time consistency
            cycle_times = [s.cycle_time_seconds for s in signals_data]
            cycle_consistency = 1.0 - (max(cycle_times) - min(cycle_times)) / max(cycle_times)
            
            # Check current coordination level
            coordinated_signals = sum(1 for s in signals_data if s.is_coordinated)
            coordination_level = coordinated_signals / len(signals_data)
            
            # Assess improvement potential
            if coordination_level > 0.8:
                potential = "High - Already well coordinated"
            elif cycle_consistency > 0.9:
                potential = "High - Consistent cycle times"
            elif cycle_consistency > 0.7:
                potential = "Medium - Some cycle time variation"
            else:
                potential = "Low - Inconsistent timing"
            
            return {
                "cycle_consistency": round(cycle_consistency, 2),
                "current_coordination_level": round(coordination_level, 2),
                "potential_rating": potential,
                "recommended_actions": self._get_coordination_recommendations(
                    cycle_consistency, coordination_level
                )
            }
            
        except Exception as e:
            logger.error(f"Coordination assessment failed: {e}")
            return {}
    
    def _get_coordination_recommendations(
        self,
        cycle_consistency: float,
        coordination_level: float
    ) -> List[str]:
        """Generate coordination improvement recommendations"""
        recommendations = []
        
        if cycle_consistency < 0.8:
            recommendations.append("Standardize signal cycle times across corridor")
        
        if coordination_level < 0.5:
            recommendations.append("Implement basic signal coordination")
        
        if coordination_level < 0.8:
            recommendations.append("Optimize signal offset timing")
        
        recommendations.append("Monitor and adjust based on traffic patterns")
        recommendations.append("Consider adaptive signal control systems")
        
        return recommendations
    
    def _generate_bandwidth_recommendations(
        self,
        optimal_analysis: Dict,
        signals_data: List
    ) -> List[str]:
        """Generate bandwidth optimization recommendations"""
        recommendations = []
        
        optimal_speed = optimal_analysis["speed_kmh"]
        efficiency = optimal_analysis["efficiency_percent"]
        
        if efficiency < 50:
            recommendations.append(f"Poor coordination - consider signal timing review")
        
        if optimal_speed < 35:
            recommendations.append("Consider increasing signal cycle times")
        elif optimal_speed > 65:
            recommendations.append("Consider reducing signal cycle times")
        
        recommendations.append(f"Target speed: {optimal_speed} km/h for optimal flow")
        
        if len(signals_data) > 5:
            recommendations.append("Consider splitting into smaller coordination groups")
        
        return recommendations
    
    def _calculate_distance(self, coord1: CoordinatesSchema, coord2: CoordinatesSchema) -> float:
        """Calculate distance between coordinates in kilometers"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1, lat2, lon2 = map(radians, [
            coord1.latitude, coord1.longitude,
            coord2.latitude, coord2.longitude
        ])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return c * 6371  # Earth's radius in km


# Global instance
green_wave_service = GreenWaveService()