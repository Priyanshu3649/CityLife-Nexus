"""
Health Impact Assessment API endpoints
Provides personalized health risk calculations and recommendations
"""
from typing import Optional, List, Tuple
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.health_impact_service import health_impact_service
from app.schemas.user import HealthProfile
from app.schemas.air_quality import RouteAQIData, HealthImpactEstimate, AQIReading
from app.schemas.base import CoordinatesSchema

router = APIRouter()


class HealthImpactRequest(BaseModel):
    """Request model for health impact calculation"""
    route_aqi_data: RouteAQIData
    health_profile: Optional[HealthProfile] = None
    travel_time_minutes: int = Field(default=30, ge=1, le=300)
    vehicle_type: str = Field(default="car", pattern="^(car|electric|motorcycle|bicycle|walking)$")


class RouteHealthComparisonRequest(BaseModel):
    """Request model for comparing health impacts between routes"""
    route1_aqi_data: RouteAQIData
    route2_aqi_data: RouteAQIData
    health_profile: Optional[HealthProfile] = None
    travel_times: Tuple[int, int] = Field(default=(30, 30))


class AQIHealthRecommendationRequest(BaseModel):
    """Request model for AQI-based health recommendations"""
    aqi: int = Field(ge=0, le=500)
    health_profile: Optional[HealthProfile] = None


@router.post("/calculate", response_model=HealthImpactEstimate)
async def calculate_health_impact(request: HealthImpactRequest):
    """
    Calculate comprehensive health impact for a route
    
    This endpoint provides personalized health risk assessment based on:
    - Air quality data along the route
    - Personal health profile (age, conditions, sensitivity)
    - Travel time and vehicle type
    - Activity level and exposure factors
    
    Returns detailed health impact estimate with risk score and precautions.
    """
    try:
        impact = health_impact_service.calculate_comprehensive_health_impact(
            route_aqi_data=request.route_aqi_data,
            health_profile=request.health_profile,
            travel_time_minutes=request.travel_time_minutes,
            vehicle_type=request.vehicle_type
        )
        return impact
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health impact calculation failed: {str(e)}")


@router.post("/compare-routes")
async def compare_route_health_impacts(request: RouteHealthComparisonRequest):
    """
    Compare health impacts between two routes
    
    Analyzes and compares the health risks of two different routes,
    providing recommendations on which route is healthier based on:
    - Air quality differences
    - Personal health profile
    - Travel time variations
    - Exposure levels and risk factors
    
    Returns detailed comparison with health benefit analysis.
    """
    try:
        comparison = health_impact_service.calculate_route_health_comparison(
            route1_data=request.route1_aqi_data,
            route2_data=request.route2_aqi_data,
            health_profile=request.health_profile,
            travel_times=request.travel_times
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route health comparison failed: {str(e)}")


@router.post("/aqi-recommendations")
async def get_aqi_health_recommendations(request: AQIHealthRecommendationRequest):
    """
    Get health recommendations for specific AQI level
    
    Provides personalized health advice and precautions based on:
    - Current AQI level
    - Personal health profile and conditions
    - Age-specific risk factors
    - Activity recommendations
    
    Returns categorized recommendations with safety guidelines.
    """
    try:
        recommendations = health_impact_service.get_health_recommendations_for_aqi(
            aqi=request.aqi,
            health_profile=request.health_profile
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health recommendations failed: {str(e)}")


@router.get("/risk-factors")
async def get_health_risk_factors():
    """
    Get information about health risk factors and calculations
    
    Returns reference information about:
    - Age group risk multipliers
    - Respiratory condition impacts
    - Pollutant health effects
    - Vehicle protection factors
    - Activity level adjustments
    
    Useful for understanding how health impacts are calculated.
    """
    try:
        return {
            "age_risk_factors": health_impact_service.age_risk_factors,
            "respiratory_conditions": health_impact_service.respiratory_conditions,
            "pollutant_impacts": health_impact_service.pollutant_impacts,
            "activity_factors": health_impact_service.activity_factors,
            "vehicle_protection": {
                "car": 0.7,
                "electric": 0.6,
                "motorcycle": 1.2,
                "bicycle": 1.3,
                "walking": 1.1
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk factors retrieval failed: {str(e)}")


@router.get("/health-categories")
async def get_aqi_health_categories():
    """
    Get AQI health category definitions and thresholds
    
    Returns standard AQI categories with:
    - AQI ranges and color codes
    - Health impact descriptions
    - General recommendations
    - Sensitive group guidelines
    
    Useful for displaying AQI information in user interfaces.
    """
    return {
        "categories": [
            {
                "range": "0-50",
                "category": "Good",
                "color": "green",
                "description": "Air quality is satisfactory for outdoor activities",
                "sensitive_groups": "None"
            },
            {
                "range": "51-100",
                "category": "Moderate",
                "color": "yellow",
                "description": "Air quality is acceptable for most people",
                "sensitive_groups": "Unusually sensitive individuals may experience minor symptoms"
            },
            {
                "range": "101-150",
                "category": "Unhealthy for Sensitive Groups",
                "color": "orange",
                "description": "Sensitive individuals should limit outdoor exposure",
                "sensitive_groups": "Children, seniors, people with respiratory/heart conditions"
            },
            {
                "range": "151-200",
                "category": "Unhealthy",
                "color": "red",
                "description": "Everyone should limit outdoor activities",
                "sensitive_groups": "Everyone may experience health effects"
            },
            {
                "range": "201-300",
                "category": "Very Unhealthy",
                "color": "purple",
                "description": "Health alert: everyone should avoid outdoor activities",
                "sensitive_groups": "Health warnings of emergency conditions"
            },
            {
                "range": "301-500",
                "category": "Hazardous",
                "color": "maroon",
                "description": "Health emergency: everyone should stay indoors",
                "sensitive_groups": "Everyone is at risk of serious health effects"
            }
        ]
    }


class PersonalizedRouteRequest(BaseModel):
    """Request for personalized route health analysis"""
    start_coordinates: CoordinatesSchema
    end_coordinates: CoordinatesSchema
    health_profile: Optional[HealthProfile] = None
    vehicle_type: str = Field(default="car")
    max_detour_minutes: int = Field(default=10, ge=0, le=30)


@router.post("/personalized-route-analysis")
async def analyze_personalized_route_health(request: PersonalizedRouteRequest):
    """
    Analyze health impacts for personalized route planning
    
    This endpoint would integrate with route planning to provide:
    - Health-optimized route suggestions
    - Personalized risk assessments
    - Alternative route health comparisons
    - Real-time health alerts
    
    Note: This is a placeholder for integration with route planning service.
    """
    # This would integrate with the route planning service
    # For now, return a structured response indicating the capability
    
    return {
        "message": "Personalized route health analysis capability",
        "request_received": {
            "start": request.start_coordinates,
            "end": request.end_coordinates,
            "health_profile_provided": request.health_profile is not None,
            "vehicle_type": request.vehicle_type,
            "max_detour": request.max_detour_minutes
        },
        "analysis_features": [
            "Health risk scoring for route segments",
            "Personalized precautions based on health profile",
            "Alternative route health comparisons",
            "Real-time air quality integration",
            "Vehicle-specific exposure calculations",
            "Time-weighted health impact assessment"
        ],
        "next_steps": [
            "Integrate with route planning service",
            "Connect to real-time AQI data sources",
            "Implement route segment health analysis",
            "Add predictive health impact modeling"
        ]
    }


# Health impact calculation utilities for other services
class HealthImpactUtils:
    """Utility functions for health impact calculations"""
    
    @staticmethod
    def quick_health_risk_score(aqi: int, has_respiratory_condition: bool = False, age_group: str = "adult") -> float:
        """Quick health risk score calculation for simple use cases"""
        base_risk = min(50, aqi * 0.3)
        
        # Age adjustment
        age_multiplier = {"child": 1.5, "adult": 1.0, "senior": 1.3}.get(age_group, 1.0)
        
        # Condition adjustment
        condition_multiplier = 2.0 if has_respiratory_condition else 1.0
        
        return min(100, base_risk * age_multiplier * condition_multiplier)
    
    @staticmethod
    def get_simple_precautions(aqi: int, has_respiratory_condition: bool = False) -> List[str]:
        """Get simple precautions based on AQI level"""
        precautions = []
        
        if aqi > 200:
            precautions.extend([
                "Air quality is very unhealthy - avoid outdoor travel",
                "Wear N95 mask if travel is necessary",
                "Keep windows closed"
            ])
        elif aqi > 150:
            precautions.extend([
                "Air quality is unhealthy - limit outdoor exposure",
                "Consider wearing a mask",
                "Avoid strenuous activity"
            ])
        elif aqi > 100:
            precautions.append("Air quality is unhealthy for sensitive groups")
            if has_respiratory_condition:
                precautions.append("Take extra precautions due to respiratory condition")
        
        return precautions


@router.get("/quick-risk-score")
async def get_quick_health_risk_score(
    aqi: int = Query(ge=0, le=500),
    has_respiratory_condition: bool = Query(default=False),
    age_group: str = Query(default="adult", regex="^(child|adult|senior)$")
):
    """
    Get quick health risk score for simple use cases
    
    Provides a simplified health risk calculation without requiring
    detailed health profile information. Useful for:
    - Quick route comparisons
    - Simple health warnings
    - Basic risk assessment
    
    Returns risk score (0-100) and basic precautions.
    """
    try:
        risk_score = HealthImpactUtils.quick_health_risk_score(
            aqi, has_respiratory_condition, age_group
        )
        precautions = HealthImpactUtils.get_simple_precautions(
            aqi, has_respiratory_condition
        )
        
        return {
            "aqi": aqi,
            "health_risk_score": round(risk_score, 1),
            "risk_level": "Low" if risk_score < 30 else "Moderate" if risk_score < 60 else "High",
            "precautions": precautions,
            "age_group": age_group,
            "has_respiratory_condition": has_respiratory_condition
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick risk calculation failed: {str(e)}")