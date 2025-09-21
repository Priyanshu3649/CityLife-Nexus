"""
Health Impact Assessment Service
Advanced health risk calculations based on air pollution exposure
"""
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.schemas.base import CoordinatesSchema
from app.schemas.user import HealthProfile
from app.schemas.air_quality import AQIReading, RouteAQIData, HealthImpactEstimate
from app.schemas.route import RouteOption

logger = logging.getLogger(__name__)


class HealthImpactService:
    """Advanced health impact assessment and risk calculation"""
    
    def __init__(self):
        # Health risk factors by age group
        self.age_risk_factors = {
            "child": {
                "base_multiplier": 1.5,
                "respiratory_sensitivity": 2.0,
                "development_risk": True,
                "recommended_aqi_limit": 100
            },
            "adult": {
                "base_multiplier": 1.0,
                "respiratory_sensitivity": 1.0,
                "development_risk": False,
                "recommended_aqi_limit": 150
            },
            "senior": {
                "base_multiplier": 1.3,
                "respiratory_sensitivity": 1.5,
                "cardiovascular_risk": True,
                "recommended_aqi_limit": 100
            }
        }
        
        # Respiratory condition risk multipliers
        self.respiratory_conditions = {
            "asthma": {"multiplier": 2.0, "critical_aqi": 100},
            "copd": {"multiplier": 2.5, "critical_aqi": 80},
            "bronchitis": {"multiplier": 1.8, "critical_aqi": 120},
            "allergies": {"multiplier": 1.4, "critical_aqi": 150},
            "lung_disease": {"multiplier": 3.0, "critical_aqi": 75}
        }
        
        # Pollutant health impact coefficients
        self.pollutant_impacts = {
            "pm25": {
                "respiratory_impact": 1.0,
                "cardiovascular_impact": 0.8,
                "cancer_risk": 0.6,
                "who_guideline": 15.0  # μg/m³ annual
            },
            "pm10": {
                "respiratory_impact": 0.7,
                "cardiovascular_impact": 0.5,
                "cancer_risk": 0.3,
                "who_guideline": 45.0  # μg/m³ annual
            },
            "no2": {
                "respiratory_impact": 0.9,
                "cardiovascular_impact": 0.4,
                "cancer_risk": 0.2,
                "who_guideline": 25.0  # μg/m³ annual
            },
            "o3": {
                "respiratory_impact": 0.8,
                "cardiovascular_impact": 0.3,
                "cancer_risk": 0.1,
                "who_guideline": 100.0  # μg/m³ 8-hour
            }
        }
        
        # Activity level exposure factors
        self.activity_factors = {
            "low": {"breathing_rate": 0.8, "exposure_time": 0.9},
            "moderate": {"breathing_rate": 1.0, "exposure_time": 1.0},
            "high": {"breathing_rate": 1.3, "exposure_time": 1.1}
        }
    
    def calculate_comprehensive_health_impact(
        self,
        route_aqi_data: RouteAQIData,
        health_profile: Optional[HealthProfile] = None,
        travel_time_minutes: int = 30,
        vehicle_type: str = "car"
    ) -> HealthImpactEstimate:
        """
        Calculate comprehensive health impact with detailed risk assessment
        """
        try:
            # Base exposure calculation
            base_exposure = self._calculate_base_exposure(
                route_aqi_data, travel_time_minutes, vehicle_type
            )
            
            # Personal risk factors
            personal_risk = self._calculate_personal_risk_factors(health_profile)
            
            # Pollutant-specific impacts
            pollutant_impacts = self._calculate_pollutant_impacts(
                route_aqi_data, health_profile
            )
            
            # Time-weighted exposure
            time_weighted_exposure = self._calculate_time_weighted_exposure(
                base_exposure, travel_time_minutes, health_profile
            )
            
            # Health risk score (0-100)
            health_risk_score = self._calculate_health_risk_score(
                base_exposure, personal_risk, pollutant_impacts, time_weighted_exposure
            )
            
            # Generate personalized precautions
            precautions = self._generate_health_precautions(
                health_risk_score, route_aqi_data, health_profile
            )
            
            # Calculate comparison to baseline
            baseline_comparison = self._calculate_baseline_comparison(
                time_weighted_exposure, travel_time_minutes
            )
            
            return HealthImpactEstimate(
                estimated_exposure_pm25=round(time_weighted_exposure.get("pm25", 0), 2),
                health_risk_score=round(health_risk_score, 1),
                recommended_precautions=precautions,
                comparison_to_baseline=round(baseline_comparison, 1)
            )
            
        except Exception as e:
            logger.error(f"Health impact calculation failed: {e}")
            return self._generate_default_health_impact(route_aqi_data.average_aqi)
    
    def _calculate_base_exposure(
        self,
        route_aqi_data: RouteAQIData,
        travel_time_minutes: int,
        vehicle_type: str
    ) -> Dict[str, float]:
        """Calculate base pollution exposure"""
        
        # Vehicle protection factors
        vehicle_protection = {
            "car": 0.7,      # Closed windows, some filtration
            "electric": 0.6,  # Better air filtration
            "motorcycle": 1.2, # Direct exposure
            "bicycle": 1.3,   # High exposure + increased breathing
            "walking": 1.1    # Direct exposure
        }
        
        protection_factor = vehicle_protection.get(vehicle_type, 0.7)
        
        # Convert AQI to estimated pollutant concentrations
        avg_aqi = route_aqi_data.average_aqi
        max_aqi = route_aqi_data.max_aqi
        
        # Simplified AQI to concentration conversion
        estimated_pm25 = self._aqi_to_pm25_concentration(avg_aqi)
        estimated_pm10 = estimated_pm25 * 1.5  # Rough ratio
        estimated_no2 = estimated_pm25 * 0.8
        estimated_o3 = estimated_pm25 * 0.6
        
        # Apply vehicle protection and time exposure
        time_factor = travel_time_minutes / 60.0  # Convert to hours
        
        base_exposure = {
            "pm25": estimated_pm25 * protection_factor * time_factor,
            "pm10": estimated_pm10 * protection_factor * time_factor,
            "no2": estimated_no2 * protection_factor * time_factor,
            "o3": estimated_o3 * protection_factor * time_factor
        }
        
        return base_exposure
    
    def _aqi_to_pm25_concentration(self, aqi: int) -> float:
        """Convert AQI to estimated PM2.5 concentration (μg/m³)"""
        # Simplified conversion based on EPA breakpoints
        if aqi <= 50:
            return aqi * 12.0 / 50.0
        elif aqi <= 100:
            return 12.0 + (aqi - 50) * 23.4 / 50.0
        elif aqi <= 150:
            return 35.4 + (aqi - 100) * 20.0 / 50.0
        elif aqi <= 200:
            return 55.4 + (aqi - 150) * 95.0 / 50.0
        else:
            return min(500, 150.4 + (aqi - 200) * 100.0 / 100.0)
    
    def _calculate_personal_risk_factors(
        self,
        health_profile: Optional[HealthProfile]
    ) -> Dict[str, float]:
        """Calculate personal health risk multipliers"""
        
        if not health_profile:
            return {"age_factor": 1.0, "condition_factor": 1.0, "sensitivity_factor": 1.0}
        
        # Age-based risk factor
        age_data = self.age_risk_factors.get(health_profile.age_group, self.age_risk_factors["adult"])
        age_factor = age_data["base_multiplier"]
        
        # Respiratory condition factor
        condition_factor = 1.0
        if health_profile.respiratory_conditions:
            max_condition_risk = 1.0
            for condition in health_profile.respiratory_conditions:
                if condition.lower() in self.respiratory_conditions:
                    condition_risk = self.respiratory_conditions[condition.lower()]["multiplier"]
                    max_condition_risk = max(max_condition_risk, condition_risk)
            condition_factor = max_condition_risk
        
        # Personal sensitivity factor
        sensitivity_factor = health_profile.pollution_sensitivity
        
        return {
            "age_factor": age_factor,
            "condition_factor": condition_factor,
            "sensitivity_factor": sensitivity_factor
        }
    
    def _calculate_pollutant_impacts(
        self,
        route_aqi_data: RouteAQIData,
        health_profile: Optional[HealthProfile]
    ) -> Dict[str, float]:
        """Calculate health impacts for specific pollutants"""
        
        impacts = {}
        
        # Get pollutant concentrations from AQI readings
        if route_aqi_data.aqi_readings:
            latest_reading = max(route_aqi_data.aqi_readings, key=lambda r: r.reading_time)
            
            for pollutant in ["pm25", "pm10", "no2", "o3"]:
                concentration = getattr(latest_reading, pollutant, None)
                if concentration:
                    pollutant_data = self.pollutant_impacts[pollutant]
                    guideline = pollutant_data["who_guideline"]
                    
                    # Calculate excess exposure above WHO guidelines
                    excess_ratio = max(0, (concentration - guideline) / guideline)
                    
                    # Calculate health impact based on pollutant type
                    respiratory_impact = excess_ratio * pollutant_data["respiratory_impact"]
                    cardiovascular_impact = excess_ratio * pollutant_data["cardiovascular_impact"]
                    
                    impacts[pollutant] = {
                        "respiratory": respiratory_impact,
                        "cardiovascular": cardiovascular_impact,
                        "excess_ratio": excess_ratio
                    }
        
        return impacts
    
    def _calculate_time_weighted_exposure(
        self,
        base_exposure: Dict[str, float],
        travel_time_minutes: int,
        health_profile: Optional[HealthProfile]
    ) -> Dict[str, float]:
        """Calculate time-weighted exposure with activity adjustments"""
        
        # Activity level adjustments
        activity_factor = 1.0
        if health_profile and health_profile.activity_level:
            activity_data = self.activity_factors.get(health_profile.activity_level, self.activity_factors["moderate"])
            activity_factor = activity_data["breathing_rate"] * activity_data["exposure_time"]
        
        # Time decay factor (longer exposure = higher impact, but not linear)
        time_factor = 1.0 + math.log(1 + travel_time_minutes / 30.0) * 0.3
        
        time_weighted = {}
        for pollutant, exposure in base_exposure.items():
            time_weighted[pollutant] = exposure * activity_factor * time_factor
        
        return time_weighted
    
    def _calculate_health_risk_score(
        self,
        base_exposure: Dict[str, float],
        personal_risk: Dict[str, float],
        pollutant_impacts: Dict[str, Dict],
        time_weighted_exposure: Dict[str, float]
    ) -> float:
        """Calculate overall health risk score (0-100)"""
        
        # Base risk from PM2.5 exposure (primary indicator)
        pm25_exposure = time_weighted_exposure.get("pm25", 0)
        base_risk = min(50, pm25_exposure * 2)  # Cap base risk at 50
        
        # Personal risk multipliers
        age_multiplier = personal_risk["age_factor"]
        condition_multiplier = personal_risk["condition_factor"]
        sensitivity_multiplier = personal_risk["sensitivity_factor"]
        
        # Combined personal risk factor
        personal_multiplier = (age_multiplier + condition_multiplier + sensitivity_multiplier) / 3
        
        # Pollutant-specific risk additions
        pollutant_risk = 0
        for pollutant, impacts in pollutant_impacts.items():
            if impacts:
                pollutant_risk += impacts.get("respiratory", 0) * 10
                pollutant_risk += impacts.get("cardiovascular", 0) * 5
        
        # Calculate final risk score
        total_risk = (base_risk * personal_multiplier) + pollutant_risk
        
        # Normalize to 0-100 scale
        return min(100, max(0, total_risk))
    
    def _generate_health_precautions(
        self,
        health_risk_score: float,
        route_aqi_data: RouteAQIData,
        health_profile: Optional[HealthProfile]
    ) -> List[str]:
        """Generate personalized health precautions"""
        
        precautions = []
        avg_aqi = route_aqi_data.average_aqi
        
        # General AQI-based precautions
        if avg_aqi > 200:
            precautions.extend([
                "Air quality is very unhealthy - consider postponing travel",
                "If travel is necessary, wear an N95 or P100 mask",
                "Keep windows closed and use recirculated air"
            ])
        elif avg_aqi > 150:
            precautions.extend([
                "Air quality is unhealthy - limit outdoor exposure",
                "Consider wearing a mask, especially if sensitive to pollution",
                "Avoid strenuous activity during travel"
            ])
        elif avg_aqi > 100:
            precautions.append("Air quality is unhealthy for sensitive groups")
        
        # Health profile-specific precautions
        if health_profile:
            # Age-specific advice
            if health_profile.age_group == "child":
                precautions.extend([
                    "Children are more sensitive to air pollution",
                    "Consider shorter exposure times when possible"
                ])
            elif health_profile.age_group == "senior":
                precautions.extend([
                    "Seniors should take extra precautions in polluted air",
                    "Monitor for respiratory or cardiovascular symptoms"
                ])
            
            # Condition-specific advice
            if health_profile.respiratory_conditions:
                precautions.extend([
                    "Keep rescue inhaler or medications accessible",
                    "Consider pre-medicating if advised by your doctor"
                ])
                
                for condition in health_profile.respiratory_conditions:
                    if condition.lower() in self.respiratory_conditions:
                        critical_aqi = self.respiratory_conditions[condition.lower()]["critical_aqi"]
                        if avg_aqi > critical_aqi:
                            precautions.append(f"AQI exceeds safe levels for {condition} - extra caution advised")
        
        # High risk score precautions
        if health_risk_score > 70:
            precautions.extend([
                "High health risk detected for this route",
                "Consider alternative transportation or timing",
                "Consult healthcare provider if symptoms develop"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_precautions = []
        for precaution in precautions:
            if precaution not in seen:
                seen.add(precaution)
                unique_precautions.append(precaution)
        
        return unique_precautions
    
    def _calculate_baseline_comparison(
        self,
        time_weighted_exposure: Dict[str, float],
        travel_time_minutes: int
    ) -> float:
        """Calculate exposure compared to clean air baseline"""
        
        # Clean air baseline (WHO guidelines for PM2.5)
        clean_air_pm25 = 15.0  # μg/m³
        baseline_exposure = clean_air_pm25 * (travel_time_minutes / 60.0) * 0.7  # Vehicle protection
        
        current_exposure = time_weighted_exposure.get("pm25", baseline_exposure)
        
        if baseline_exposure > 0:
            percentage_increase = ((current_exposure - baseline_exposure) / baseline_exposure) * 100
            return max(-50, min(500, percentage_increase))  # Cap between -50% and 500%
        
        return 0.0
    
    def _generate_default_health_impact(self, aqi: int) -> HealthImpactEstimate:
        """Generate default health impact when calculation fails"""
        
        # Simple fallback calculation
        if aqi <= 50:
            risk_score = 15.0
            precautions = ["Air quality is good for travel"]
        elif aqi <= 100:
            risk_score = 30.0
            precautions = ["Air quality is acceptable for most people"]
        elif aqi <= 150:
            risk_score = 50.0
            precautions = ["Sensitive individuals should limit outdoor exposure"]
        else:
            risk_score = 75.0
            precautions = ["Air quality is unhealthy - take precautions"]
        
        return HealthImpactEstimate(
            estimated_exposure_pm25=float(aqi * 0.5),
            health_risk_score=risk_score,
            recommended_precautions=precautions,
            comparison_to_baseline=float((aqi - 50) * 2)
        )
    
    def calculate_route_health_comparison(
        self,
        route1_data: RouteAQIData,
        route2_data: RouteAQIData,
        health_profile: Optional[HealthProfile] = None,
        travel_times: Tuple[int, int] = (30, 30)
    ) -> Dict[str, any]:
        """Compare health impacts between two routes"""
        
        try:
            impact1 = self.calculate_comprehensive_health_impact(
                route1_data, health_profile, travel_times[0]
            )
            
            impact2 = self.calculate_comprehensive_health_impact(
                route2_data, health_profile, travel_times[1]
            )
            
            # Determine healthier route
            if impact1.health_risk_score < impact2.health_risk_score:
                recommendation = "route1"
                health_benefit = impact2.health_risk_score - impact1.health_risk_score
            elif impact2.health_risk_score < impact1.health_risk_score:
                recommendation = "route2"
                health_benefit = impact1.health_risk_score - impact2.health_risk_score
            else:
                recommendation = "similar"
                health_benefit = 0
            
            return {
                "route1_impact": impact1,
                "route2_impact": impact2,
                "recommendation": recommendation,
                "health_benefit_score": round(health_benefit, 1),
                "exposure_difference_pm25": abs(
                    impact1.estimated_exposure_pm25 - impact2.estimated_exposure_pm25
                ),
                "summary": self._generate_comparison_summary(
                    impact1, impact2, recommendation, health_benefit
                )
            }
            
        except Exception as e:
            logger.error(f"Route health comparison failed: {e}")
            return {"error": str(e)}
    
    def _generate_comparison_summary(
        self,
        impact1: HealthImpactEstimate,
        impact2: HealthImpactEstimate,
        recommendation: str,
        health_benefit: float
    ) -> str:
        """Generate human-readable comparison summary"""
        
        if recommendation == "route1":
            return f"Route 1 is healthier with {health_benefit:.1f} points lower health risk"
        elif recommendation == "route2":
            return f"Route 2 is healthier with {health_benefit:.1f} points lower health risk"
        else:
            return "Both routes have similar health impacts"
    
    def get_health_recommendations_for_aqi(
        self,
        aqi: int,
        health_profile: Optional[HealthProfile] = None
    ) -> Dict[str, any]:
        """Get health recommendations for a specific AQI level"""
        
        # AQI category and basic info
        if aqi <= 50:
            category = "Good"
            color = "green"
            general_advice = "Air quality is satisfactory for outdoor activities"
        elif aqi <= 100:
            category = "Moderate"
            color = "yellow"
            general_advice = "Air quality is acceptable for most people"
        elif aqi <= 150:
            category = "Unhealthy for Sensitive Groups"
            color = "orange"
            general_advice = "Sensitive individuals should limit outdoor exposure"
        elif aqi <= 200:
            category = "Unhealthy"
            color = "red"
            general_advice = "Everyone should limit outdoor activities"
        elif aqi <= 300:
            category = "Very Unhealthy"
            color = "purple"
            general_advice = "Health alert: everyone should avoid outdoor activities"
        else:
            category = "Hazardous"
            color = "maroon"
            general_advice = "Health emergency: everyone should stay indoors"
        
        # Personalized recommendations
        personal_recommendations = []
        if health_profile:
            age_data = self.age_risk_factors.get(health_profile.age_group, self.age_risk_factors["adult"])
            if aqi > age_data["recommended_aqi_limit"]:
                personal_recommendations.append(f"AQI exceeds recommended limit for {health_profile.age_group}s")
            
            for condition in health_profile.respiratory_conditions or []:
                if condition.lower() in self.respiratory_conditions:
                    critical_aqi = self.respiratory_conditions[condition.lower()]["critical_aqi"]
                    if aqi > critical_aqi:
                        personal_recommendations.append(f"Take extra precautions due to {condition}")
        
        return {
            "aqi": aqi,
            "category": category,
            "color": color,
            "general_advice": general_advice,
            "personal_recommendations": personal_recommendations,
            "mask_recommended": aqi > 100,
            "outdoor_exercise_safe": aqi <= 100,
            "window_ventilation_safe": aqi <= 50
        }


# Global instance
health_impact_service = HealthImpactService()