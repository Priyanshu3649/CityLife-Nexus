"""
Multi-objective route optimization service
Integrates traffic signals, air quality, and user preferences
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import math

from app.schemas.base import CoordinatesSchema
from app.schemas.route import RouteOption, RouteComparison, RouteSegment
from app.schemas.user import UserPreferences, HealthProfile
from app.schemas.air_quality import RouteAQIData, HealthImpactEstimate
from app.services.maps_service import maps_service
from app.services.aqi_service import aqi_service
from app.services.traffic_signal_service import traffic_signal_service

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """Advanced route optimization with multi-objective scoring"""
    
    def __init__(self):
        # Default scoring weights
        self.default_weights = {
            "time": 0.4,
            "air_quality": 0.4,
            "safety": 0.2,
            "fuel_efficiency": 0.3,
            "green_wave": 0.2,
            "comfort": 0.1
        }
        
        # Route type configurations
        self.route_types = {
            "fastest": {"time": 0.8, "air_quality": 0.1, "safety": 0.1},
            "cleanest": {"time": 0.2, "air_quality": 0.7, "safety": 0.1},
            "safest": {"time": 0.2, "air_quality": 0.3, "safety": 0.5},
            "balanced": {"time": 0.4, "air_quality": 0.4, "safety": 0.2},
            "eco_friendly": {"time": 0.2, "air_quality": 0.5, "fuel_efficiency": 0.3}
        }
    
    async def optimize_route(
        self,
        origin: CoordinatesSchema,
        destination: CoordinatesSchema,
        user_preferences: Optional[UserPreferences] = None,
        health_profile: Optional[HealthProfile] = None,
        departure_time: Optional[datetime] = None,
        route_type: str = "balanced"
    ) -> List[RouteOption]:
        """
        Find and score optimal routes based on multiple objectives
        """
        try:
            # Get multiple route options from Google Maps
            base_routes = await maps_service.get_multiple_route_options(
                origin=origin,
                destination=destination,
                departure_time=departure_time
            )
            
            if not base_routes:
                logger.warning("No base routes found from Maps service")
                return []
            
            # Enhance routes with additional data and scoring
            enhanced_routes = []
            
            for route in base_routes:
                try:
                    enhanced_route = await self._enhance_route_with_data(
                        route=route,
                        user_preferences=user_preferences,
                        health_profile=health_profile,
                        departure_time=departure_time,
                        route_type=route_type
                    )
                    
                    if enhanced_route:
                        enhanced_routes.append(enhanced_route)
                        
                except Exception as e:
                    logger.error(f"Failed to enhance route {route.id}: {e}")
                    continue
            
            # Sort routes by score (highest first)
            enhanced_routes.sort(key=lambda r: r.route_score or 0, reverse=True)
            
            return enhanced_routes
            
        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            return []
    
    async def _enhance_route_with_data(
        self,
        route: RouteOption,
        user_preferences: Optional[UserPreferences],
        health_profile: Optional[HealthProfile],
        departure_time: Optional[datetime],
        route_type: str
    ) -> Optional[RouteOption]:
        """
        Enhance a route with AQI data, traffic signals, and scoring
        """
        try:
            # Get air quality data for the route
            route_aqi_data = await aqi_service.get_route_aqi_data(
                route_coordinates=route.waypoints,
                radius_km=1.0
            )
            
            # Get traffic signals along the route
            route_signals = traffic_signal_service.get_signals_along_route(
                route_coordinates=route.waypoints,
                buffer_meters=150.0
            )
            
            # Calculate health impact
            health_impact = None
            if health_profile:
                health_impact = aqi_service.calculate_health_impact(
                    route_aqi_data=route_aqi_data,
                    health_profile=health_profile,
                    travel_time_minutes=route.estimated_time_minutes
                )
            
            # Calculate green wave efficiency
            green_wave_score = self._calculate_green_wave_score(
                route_signals=route_signals,
                route_distance_km=route.distance_km,
                estimated_time_minutes=route.estimated_time_minutes
            )
            
            # Calculate comprehensive route score
            route_score = self._calculate_route_score(
                route=route,
                route_aqi_data=route_aqi_data,
                health_impact=health_impact,
                green_wave_score=green_wave_score,
                user_preferences=user_preferences,
                route_type=route_type
            )
            
            # Update route with enhanced data
            enhanced_route = RouteOption(
                id=route.id,
                start_coords=route.start_coords,
                end_coords=route.end_coords,
                waypoints=route.waypoints,
                distance_km=route.distance_km,
                estimated_time_minutes=route.estimated_time_minutes,
                average_aqi=route_aqi_data.average_aqi,
                route_score=route_score,
                route_type=route_type,
                segments=self._create_enhanced_segments(
                    route.segments or [],
                    route_aqi_data,
                    route_signals
                )
            )
            
            return enhanced_route
            
        except Exception as e:
            logger.error(f"Failed to enhance route: {e}")
            return None
    
    def _calculate_route_score(
        self,
        route: RouteOption,
        route_aqi_data: RouteAQIData,
        health_impact: Optional[HealthImpactEstimate],
        green_wave_score: float,
        user_preferences: Optional[UserPreferences],
        route_type: str
    ) -> float:
        """
        Calculate comprehensive route score (0-100)
        """
        try:
            # Get scoring weights
            weights = self._get_scoring_weights(user_preferences, route_type)
            
            # Calculate individual component scores (0-100 scale)
            time_score = self._calculate_time_score(route.estimated_time_minutes)
            aqi_score = self._calculate_aqi_score(route_aqi_data.average_aqi)
            safety_score = self._calculate_safety_score(route, route_aqi_data)
            fuel_score = self._calculate_fuel_efficiency_score(route, green_wave_score)
            comfort_score = self._calculate_comfort_score(route, route_aqi_data)
            
            # Apply weights and calculate final score
            weighted_score = (
                time_score * weights.get("time", 0.4) +
                aqi_score * weights.get("air_quality", 0.4) +
                safety_score * weights.get("safety", 0.2) +
                fuel_score * weights.get("fuel_efficiency", 0.0) +
                green_wave_score * weights.get("green_wave", 0.0) +
                comfort_score * weights.get("comfort", 0.0)
            )
            
            # Apply health impact penalty if available
            if health_impact:
                health_penalty = min(20, health_impact.health_risk_score / 5)
                weighted_score = max(0, weighted_score - health_penalty)
            
            return round(min(100, max(0, weighted_score)), 1)
            
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            return 50.0  # Default neutral score
    
    def _get_scoring_weights(
        self,
        user_preferences: Optional[UserPreferences],
        route_type: str
    ) -> Dict[str, float]:
        """
        Get scoring weights based on user preferences and route type
        """
        # Start with route type weights
        weights = self.route_types.get(route_type, self.default_weights).copy()
        
        # Override with user preferences if available
        if user_preferences:
            weights["time"] = user_preferences.prioritize_time
            weights["air_quality"] = user_preferences.prioritize_air_quality
            weights["safety"] = user_preferences.prioritize_safety
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def _calculate_time_score(self, estimated_time_minutes: int) -> float:
        """
        Calculate time efficiency score (0-100)
        Lower time = higher score
        """
        # Assume baseline of 60 minutes for scoring
        baseline_minutes = 60
        
        if estimated_time_minutes <= 10:
            return 100.0
        elif estimated_time_minutes >= baseline_minutes:
            return 20.0
        else:
            # Linear scale from 100 to 20
            return 100 - (estimated_time_minutes - 10) * 80 / (baseline_minutes - 10)
    
    def _calculate_aqi_score(self, average_aqi: int) -> float:
        """
        Calculate air quality score (0-100)
        Lower AQI = higher score
        """
        if average_aqi <= 50:  # Good
            return 100.0
        elif average_aqi <= 100:  # Moderate
            return 80 - (average_aqi - 50) * 30 / 50
        elif average_aqi <= 150:  # Unhealthy for sensitive groups
            return 50 - (average_aqi - 100) * 30 / 50
        elif average_aqi <= 200:  # Unhealthy
            return 20 - (average_aqi - 150) * 15 / 50
        else:  # Very unhealthy or hazardous
            return max(0, 5 - (average_aqi - 200) * 5 / 100)
    
    def _calculate_safety_score(
        self,
        route: RouteOption,
        route_aqi_data: RouteAQIData
    ) -> float:
        """
        Calculate safety score based on various factors
        """
        base_score = 70.0  # Base safety score
        
        # Penalty for pollution hotspots
        hotspot_penalty = len(route_aqi_data.pollution_hotspots) * 5
        
        # Bonus for shorter routes (less exposure time)
        if route.distance_km < 5:
            distance_bonus = 10
        elif route.distance_km > 20:
            distance_bonus = -10
        else:
            distance_bonus = 0
        
        # Route type bonus (highways might be safer but more polluted)
        route_type_bonus = 0
        if route.route_type == "clean":
            route_type_bonus = 15  # Avoiding highways
        elif route.route_type == "fast":
            route_type_bonus = 5   # Highways are generally safer
        
        safety_score = base_score - hotspot_penalty + distance_bonus + route_type_bonus
        
        return max(0, min(100, safety_score))
    
    def _calculate_fuel_efficiency_score(
        self,
        route: RouteOption,
        green_wave_score: float
    ) -> float:
        """
        Calculate fuel efficiency score
        """
        base_score = 60.0
        
        # Distance efficiency (shorter is better)
        if route.distance_km < 5:
            distance_score = 20
        elif route.distance_km > 15:
            distance_score = -10
        else:
            distance_score = 10
        
        # Green wave bonus (fewer stops = better fuel efficiency)
        green_wave_bonus = green_wave_score * 0.3
        
        # Speed consistency bonus (estimated from time vs distance)
        avg_speed = route.distance_km / (route.estimated_time_minutes / 60.0)
        if 40 <= avg_speed <= 60:  # Optimal speed range
            speed_bonus = 15
        elif avg_speed < 30 or avg_speed > 80:
            speed_bonus = -10
        else:
            speed_bonus = 5
        
        fuel_score = base_score + distance_score + green_wave_bonus + speed_bonus
        
        return max(0, min(100, fuel_score))
    
    def _calculate_comfort_score(
        self,
        route: RouteOption,
        route_aqi_data: RouteAQIData
    ) -> float:
        """
        Calculate comfort score based on air quality and route characteristics
        """
        base_score = 60.0
        
        # Air quality comfort
        aqi_comfort = self._calculate_aqi_score(route_aqi_data.average_aqi) * 0.4
        
        # Route length comfort (not too long, not too short)
        if 5 <= route.distance_km <= 15:
            length_comfort = 20
        elif route.distance_km < 2:
            length_comfort = -5  # Too short might mean congested local roads
        else:
            length_comfort = max(-15, 20 - (route.distance_km - 15) * 2)
        
        # Time comfort (reasonable travel time)
        time_comfort = max(-10, 15 - max(0, route.estimated_time_minutes - 30) * 0.5)
        
        comfort_score = base_score + aqi_comfort + length_comfort + time_comfort
        
        return max(0, min(100, comfort_score))
    
    def _calculate_green_wave_score(
        self,
        route_signals: List,
        route_distance_km: float,
        estimated_time_minutes: int
    ) -> float:
        """
        Calculate green wave efficiency score
        """
        if not route_signals:
            return 70.0  # Neutral score for routes without signals
        
        # Count coordinated signals
        coordinated_signals = sum(1 for signal in route_signals if signal.is_coordinated)
        coordination_ratio = coordinated_signals / len(route_signals)
        
        # Base score from coordination
        base_score = 30 + (coordination_ratio * 50)
        
        # Signal density factor
        signals_per_km = len(route_signals) / route_distance_km
        if signals_per_km < 2:  # Low density is good
            density_bonus = 15
        elif signals_per_km > 5:  # High density is challenging
            density_bonus = -10
        else:
            density_bonus = 5
        
        # Speed consistency factor
        avg_speed = route_distance_km / (estimated_time_minutes / 60.0)
        if 45 <= avg_speed <= 55:  # Optimal for green waves
            speed_bonus = 10
        else:
            speed_bonus = max(-10, 10 - abs(avg_speed - 50) * 0.5)
        
        green_wave_score = base_score + density_bonus + speed_bonus
        
        return max(0, min(100, green_wave_score))
    
    def _create_enhanced_segments(
        self,
        base_segments: List[RouteSegment],
        route_aqi_data: RouteAQIData,
        route_signals: List
    ) -> List[RouteSegment]:
        """
        Enhance route segments with AQI and traffic signal data
        """
        if not base_segments:
            return []
        
        enhanced_segments = []
        
        for i, segment in enumerate(base_segments):
            # Find AQI data for this segment
            segment_aqi = route_aqi_data.average_aqi  # Simplified - use route average
            
            # Find traffic signals in this segment
            segment_signals = []
            for signal in route_signals:
                # Check if signal is close to segment
                segment_center_lat = (segment.start_point.latitude + segment.end_point.latitude) / 2
                segment_center_lng = (segment.start_point.longitude + segment.end_point.longitude) / 2
                
                signal_distance = self._calculate_distance(
                    CoordinatesSchema(latitude=segment_center_lat, longitude=segment_center_lng),
                    signal.coordinates
                )
                
                if signal_distance <= 0.2:  # Within 200m
                    segment_signals.append(signal.signal_id)
            
            enhanced_segment = RouteSegment(
                start_point=segment.start_point,
                end_point=segment.end_point,
                distance_meters=segment.distance_meters,
                aqi_level=segment_aqi,
                traffic_signals=segment_signals,
                estimated_travel_time=segment.estimated_travel_time
            )
            
            enhanced_segments.append(enhanced_segment)
        
        return enhanced_segments
    
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
    
    async def compare_routes(
        self,
        origin: CoordinatesSchema,
        destination: CoordinatesSchema,
        user_preferences: Optional[UserPreferences] = None,
        health_profile: Optional[HealthProfile] = None,
        departure_time: Optional[datetime] = None
    ) -> Optional[RouteComparison]:
        """
        Compare different route types and provide recommendations
        """
        try:
            # Get optimized routes for different types
            fastest_routes = await self.optimize_route(
                origin, destination, user_preferences, health_profile, 
                departure_time, "fastest"
            )
            
            cleanest_routes = await self.optimize_route(
                origin, destination, user_preferences, health_profile, 
                departure_time, "cleanest"
            )
            
            balanced_routes = await self.optimize_route(
                origin, destination, user_preferences, health_profile, 
                departure_time, "balanced"
            )
            
            # Select best route from each category
            fast_route = fastest_routes[0] if fastest_routes else None
            clean_route = cleanest_routes[0] if cleanest_routes else None
            balanced_route = balanced_routes[0] if balanced_routes else None
            
            if not (fast_route and clean_route):
                return None
            
            # Determine recommendation based on user preferences
            recommendation = self._determine_recommendation(
                fast_route, clean_route, balanced_route, user_preferences
            )
            
            return RouteComparison(
                fast_route=fast_route,
                clean_route=clean_route,
                balanced_route=balanced_route,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Route comparison failed: {e}")
            return None
    
    def _determine_recommendation(
        self,
        fast_route: RouteOption,
        clean_route: RouteOption,
        balanced_route: Optional[RouteOption],
        user_preferences: Optional[UserPreferences]
    ) -> str:
        """
        Determine which route to recommend based on preferences and scores
        """
        if not user_preferences:
            return "balanced" if balanced_route else "fast"
        
        time_priority = user_preferences.prioritize_time
        aqi_priority = user_preferences.prioritize_air_quality
        
        # Strong preference for time
        if time_priority > 0.6:
            return "fast"
        
        # Strong preference for air quality
        if aqi_priority > 0.6:
            return "clean"
        
        # Compare scores if balanced route exists
        if balanced_route:
            scores = {
                "fast": fast_route.route_score or 0,
                "clean": clean_route.route_score or 0,
                "balanced": balanced_route.route_score or 0
            }
            return max(scores, key=scores.get)
        
        # Compare time vs AQI difference
        time_diff_percent = abs(fast_route.estimated_time_minutes - clean_route.estimated_time_minutes) / fast_route.estimated_time_minutes
        aqi_diff_percent = abs((fast_route.average_aqi or 100) - (clean_route.average_aqi or 100)) / (fast_route.average_aqi or 100)
        
        if aqi_diff_percent > time_diff_percent * 2:
            return "clean"
        else:
            return "fast"
    
    async def calculate_route_efficiency_metrics(
        self,
        route: RouteOption,
        baseline_route: Optional[RouteOption] = None
    ) -> Dict[str, Any]:
        """
        Calculate efficiency metrics for a route
        """
        try:
            metrics = {
                "route_id": str(route.id),
                "distance_km": route.distance_km,
                "estimated_time_minutes": route.estimated_time_minutes,
                "average_speed_kmh": route.distance_km / (route.estimated_time_minutes / 60.0),
                "route_score": route.route_score,
                "average_aqi": route.average_aqi
            }
            
            # Calculate efficiency ratios
            if baseline_route:
                metrics["time_efficiency"] = baseline_route.estimated_time_minutes / route.estimated_time_minutes
                metrics["distance_efficiency"] = baseline_route.distance_km / route.distance_km
                
                if baseline_route.average_aqi and route.average_aqi:
                    metrics["aqi_improvement"] = (baseline_route.average_aqi - route.average_aqi) / baseline_route.average_aqi
            
            # Estimate fuel consumption (simplified)
            base_consumption = route.distance_km * 0.08  # 8L/100km baseline
            
            # Adjust for speed efficiency
            avg_speed = metrics["average_speed_kmh"]
            if avg_speed < 30:
                speed_factor = 1.3  # City driving penalty
            elif avg_speed > 80:
                speed_factor = 1.2  # High speed penalty
            else:
                speed_factor = 1.0
            
            metrics["estimated_fuel_liters"] = round(base_consumption * speed_factor, 2)
            
            # Estimate CO2 emissions (2.3 kg CO2 per liter of fuel)
            metrics["estimated_co2_kg"] = round(metrics["estimated_fuel_liters"] * 2.3, 2)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Metrics calculation failed: {e}")
            return {"error": str(e)}


# Global instance
route_optimizer = RouteOptimizer()