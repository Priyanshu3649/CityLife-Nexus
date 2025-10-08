"""
Eco-Score service for calculating trip environmental impact and health benefits
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from app.schemas.base import CoordinatesSchema

logger = logging.getLogger(__name__)


class TripLog:
    """Represents a log entry for a segment of a trip"""
    
    def __init__(
        self,
        segment_id: str,
        start_coords: CoordinatesSchema,
        end_coords: CoordinatesSchema,
        travel_time_seconds: float,
        aqi_exposure: float,  # Average AQI during this segment
        signals_crossed: int,
        signals_on_green: int,
        idling_time_seconds: float,
        distance_meters: float
    ):
        self.segment_id = segment_id
        self.start_coords = start_coords
        self.end_coords = end_coords
        self.travel_time_seconds = travel_time_seconds
        self.aqi_exposure = aqi_exposure
        self.signals_crossed = signals_crossed
        self.signals_on_green = signals_on_green
        self.idling_time_seconds = idling_time_seconds
        self.distance_meters = distance_meters
        self.timestamp = datetime.utcnow()


class EcoScoreService:
    """Service for calculating Eco-Scores and trip health reports"""
    
    def __init__(self):
        self.trip_logs = {}  # In-memory storage for demo
        self.baseline_data = self._initialize_baseline_data()
    
    def _initialize_baseline_data(self) -> Dict[str, Any]:
        """Initialize baseline data for comparison"""
        return {
            "baseline_idling_per_signal": 30.0,  # seconds
            "baseline_fuel_consumption_per_km": 0.08,  # liters per km
            "baseline_pollution_exposure": 150.0,  # avg AQI
            "fuel_saved_per_green_signal": 0.0005  # liters
        }
    
    async def calculate_eco_score(
        self,
        trip_id: str,
        trip_logs: List[TripLog],
        vehicle_type: str = "car"
    ) -> Dict[str, Any]:
        """
        Calculate Eco-Score for a completed trip
        
        Args:
            trip_id: Unique identifier for the trip
            trip_logs: List of trip segment logs
            vehicle_type: Type of vehicle used
            
        Returns:
            Dictionary with Eco-Score metrics
        """
        if not trip_logs:
            return self._create_empty_eco_score()
        
        # Calculate metrics
        total_signals_crossed = sum(log.signals_crossed for log in trip_logs)
        total_signals_on_green = sum(log.signals_on_green for log in trip_logs)
        total_idling_time = sum(log.idling_time_seconds for log in trip_logs)
        total_distance_km = sum(log.distance_meters for log in trip_logs) / 1000
        total_travel_time = sum(log.travel_time_seconds for log in trip_logs)
        
        # Pollution exposure calculations
        pollution_dose = sum(log.aqi_exposure * (log.travel_time_seconds / 3600) for log in trip_logs)
        avg_aqi_exposure = pollution_dose / (total_travel_time / 3600) if total_travel_time > 0 else 0
        
        # Fuel consumption calculations
        baseline_fuel_consumption = total_distance_km * self.baseline_data["baseline_fuel_consumption_per_km"]
        fuel_saved_from_green_signals = total_signals_on_green * self.baseline_data["fuel_saved_per_green_signal"]
        actual_fuel_consumption = max(0, baseline_fuel_consumption - fuel_saved_from_green_signals)
        
        # Efficiency calculations
        green_signal_ratio = (total_signals_on_green / total_signals_crossed) if total_signals_crossed > 0 else 0
        idling_efficiency = 1.0 - min(1.0, total_idling_time / (total_signals_crossed * self.baseline_data["baseline_idling_per_signal"])) if total_signals_crossed > 0 else 1.0
        
        # Eco-Score calculation (0-100)
        # Weighted score based on multiple factors
        green_signal_score = green_signal_ratio * 40  # 40% weight
        pollution_score = max(0, (1 - (avg_aqi_exposure / self.baseline_data["baseline_pollution_exposure"])) * 30)  # 30% weight
        idling_score = idling_efficiency * 20  # 20% weight
        fuel_efficiency_score = min(100, (baseline_fuel_consumption / actual_fuel_consumption) * 10) if actual_fuel_consumption > 0 else 10  # 10% weight
        
        eco_score = green_signal_score + pollution_score + idling_score + fuel_efficiency_score
        eco_score = max(0, min(100, eco_score))  # Clamp between 0-100
        
        # Create result dictionary
        result = {
            "trip_id": trip_id,
            "eco_score": round(eco_score, 1),
            "metrics": {
                "signals_crossed": total_signals_crossed,
                "signals_on_green": total_signals_on_green,
                "green_signal_percentage": round(green_signal_ratio * 100, 1),
                "total_idling_time_seconds": round(total_idling_time, 1),
                "idling_efficiency": round(idling_efficiency * 100, 1),
                "total_distance_km": round(total_distance_km, 2),
                "total_travel_time_minutes": round(total_travel_time / 60, 1),
                "avg_aqi_exposure": round(avg_aqi_exposure, 1),
                "pollution_dose": round(pollution_dose, 2),
                "baseline_fuel_consumption_liters": round(baseline_fuel_consumption, 3),
                "actual_fuel_consumption_liters": round(actual_fuel_consumption, 3),
                "fuel_saved_liters": round(baseline_fuel_consumption - actual_fuel_consumption, 3),
                "fuel_efficiency_improvement": round(((baseline_fuel_consumption - actual_fuel_consumption) / baseline_fuel_consumption * 100) if baseline_fuel_consumption > 0 else 0, 1)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store the result
        self.trip_logs[trip_id] = result
        
        return result
    
    def _create_empty_eco_score(self) -> Dict[str, Any]:
        """Create an empty Eco-Score result"""
        return {
            "trip_id": "",
            "eco_score": 0.0,
            "metrics": {
                "signals_crossed": 0,
                "signals_on_green": 0,
                "green_signal_percentage": 0.0,
                "total_idling_time_seconds": 0.0,
                "idling_efficiency": 0.0,
                "total_distance_km": 0.0,
                "total_travel_time_minutes": 0.0,
                "avg_aqi_exposure": 0.0,
                "pollution_dose": 0.0,
                "baseline_fuel_consumption_liters": 0.0,
                "actual_fuel_consumption_liters": 0.0,
                "fuel_saved_liters": 0.0,
                "fuel_efficiency_improvement": 0.0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_trip_comparison(
        self,
        trip_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple trips
        
        Args:
            trip_ids: List of trip IDs to compare
            
        Returns:
            Dictionary with comparison data
        """
        trips_data = []
        for trip_id in trip_ids:
            if trip_id in self.trip_logs:
                trips_data.append(self.trip_logs[trip_id])
        
        if not trips_data:
            return {"comparison": [], "summary": {}}
        
        # Calculate averages
        avg_eco_score = sum(trip["eco_score"] for trip in trips_data) / len(trips_data)
        avg_green_signal_pct = sum(trip["metrics"]["green_signal_percentage"] for trip in trips_data) / len(trips_data)
        avg_fuel_saved = sum(trip["metrics"]["fuel_saved_liters"] for trip in trips_data) / len(trips_data)
        avg_pollution_reduction = sum(
            (self.baseline_data["baseline_pollution_exposure"] - trip["metrics"]["avg_aqi_exposure"]) 
            for trip in trips_data
        ) / len(trips_data)
        
        return {
            "comparison": trips_data,
            "summary": {
                "average_eco_score": round(avg_eco_score, 1),
                "average_green_signal_percentage": round(avg_green_signal_pct, 1),
                "average_fuel_saved_liters": round(avg_fuel_saved, 3),
                "average_pollution_reduction": round(avg_pollution_reduction, 1),
                "total_trips": len(trips_data)
            }
        }
    
    async def get_user_eco_statistics(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get overall Eco-Score statistics for a user
        
        Args:
            user_id: Optional user ID (for multi-user support)
            
        Returns:
            Dictionary with user statistics
        """
        # For demo, we'll use all trips
        all_trip_scores = [trip["eco_score"] for trip in self.trip_logs.values()]
        
        if not all_trip_scores:
            return {
                "total_trips": 0,
                "average_eco_score": 0.0,
                "best_trip_score": 0.0,
                "worst_trip_score": 0.0,
                "total_fuel_saved_liters": 0.0,
                "total_pollution_avoided": 0.0
            }
        
        total_fuel_saved = sum(
            trip["metrics"]["fuel_saved_liters"] 
            for trip in self.trip_logs.values()
        )
        
        total_pollution_avoided = sum(
            (self.baseline_data["baseline_pollution_exposure"] - trip["metrics"]["avg_aqi_exposure"]) * 
            (trip["metrics"]["total_travel_time_minutes"] / 60)
            for trip in self.trip_logs.values()
        )
        
        return {
            "total_trips": len(all_trip_scores),
            "average_eco_score": round(sum(all_trip_scores) / len(all_trip_scores), 1),
            "best_trip_score": round(max(all_trip_scores), 1),
            "worst_trip_score": round(min(all_trip_scores), 1),
            "total_fuel_saved_liters": round(total_fuel_saved, 3),
            "total_pollution_avoided": round(total_pollution_avoided, 2)  # In AQI*hours
        }
    
    async def get_eco_score_recommendations(
        self,
        eco_score_result: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on Eco-Score result
        
        Args:
            eco_score_result: Eco-Score calculation result
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        metrics = eco_score_result.get("metrics", {})
        
        # Green signal recommendations
        green_pct = metrics.get("green_signal_percentage", 0)
        if green_pct < 50:
            recommendations.append("Try to time your departure to catch more green signals")
        elif green_pct < 70:
            recommendations.append("Good job catching green signals! Try to improve further")
        
        # Idling recommendations
        idling_efficiency = metrics.get("idling_efficiency", 0)
        if idling_efficiency < 70:
            recommendations.append("Reduce idling time at signals to save fuel and reduce emissions")
        
        # Pollution recommendations
        avg_aqi = metrics.get("avg_aqi_exposure", 0)
        if avg_aqi > 150:
            recommendations.append("Consider routes with better air quality on future trips")
        
        # Fuel efficiency recommendations
        fuel_improvement = metrics.get("fuel_efficiency_improvement", 0)
        if fuel_improvement < 10:
            recommendations.append("Optimize your driving habits to improve fuel efficiency")
        
        # General encouragement
        eco_score = eco_score_result.get("eco_score", 0)
        if eco_score >= 80:
            recommendations.append("Excellent Eco-Score! You're making a positive environmental impact")
        elif eco_score >= 60:
            recommendations.append("Good Eco-Score! Keep up the environmentally conscious driving")
        
        return recommendations


# Global instance
eco_score_service = EcoScoreService()