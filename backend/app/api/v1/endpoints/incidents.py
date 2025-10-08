"""
Incidents and emergency API endpoints for auto-rerouting
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.community_service import community_service
from app.services.aqi_service import aqi_service
from app.schemas.base import CoordinatesSchema
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.get("/live")
async def get_live_incidents(
    center: Optional[CoordinatesSchema] = None,
    radius_km: float = Query(10.0, ge=1.0, le=50.0, description="Search radius in kilometers")
):
    """
    Get live incidents and reports that might affect routing
    
    Args:
        center: Center coordinates for search (optional, defaults to Delhi NCR)
        radius_km: Search radius in kilometers
        
    Returns:
        Live incidents and reports
    """
    # If no center provided, use Delhi NCR center
    if center is None:
        center = CoordinatesSchema(latitude=28.6139, longitude=77.2090)  # Connaught Place, Delhi
    
    # Get community reports
    reports = await community_service.get_reports_in_area(
        center=center,
        radius_km=radius_km,
        min_trust_score=0.5
    )
    
    # Filter for active incidents that might affect routing
    incident_types = ["accident", "road_hazard", "construction", "weather_impact"]
    active_incidents = [
        report for report in reports 
        if report["report_type"] in incident_types and report["is_active"]
    ]
    
    # Get high AQI areas that might trigger rerouting
    try:
        aqi_readings = await aqi_service.get_measurements_by_location(
            coordinates=center,
            radius_km=radius_km
        )
        
        # Filter for hazardous AQI levels (>200)
        hazardous_aqi_areas = [
            reading for reading in aqi_readings 
            if reading.aqi_value > 200
        ]
    except Exception as e:
        hazardous_aqi_areas = []
        print(f"Error fetching AQI data: {e}")
    
    return {
        "center": center,
        "radius_km": radius_km,
        "timestamp": datetime.utcnow().isoformat(),
        "active_incidents": active_incidents,
        "hazardous_aqi_areas": hazardous_aqi_areas,
        "total_incidents": len(active_incidents),
        "total_hazardous_areas": len(hazardous_aqi_areas)
    }


@router.post("/trigger-reroute")
async def trigger_emergency_reroute(
    current_location: CoordinatesSchema,
    destination: CoordinatesSchema,
    incident_location: CoordinatesSchema,
    incident_type: str = Query(..., regex="^(accident|aqi_spike|road_closure|weather)$"),
    severity: str = Query("high", regex="^(medium|high|critical)$")
):
    """
    Trigger emergency reroute based on incident
    
    Args:
        current_location: Current vehicle location
        destination: Original destination
        incident_location: Location of the incident
        incident_type: Type of incident
        severity: Severity of the incident
        
    Returns:
        Reroute recommendation
    """
    # Calculate distance to incident
    from app.services.maps_service import maps_service
    distance_to_incident = maps_service.calculate_distance_between_points(
        current_location, incident_location
    )
    
    # Determine if reroute is needed based on severity and proximity
    should_reroute = False
    reason = ""
    
    if incident_type == "accident" and severity in ["high", "critical"]:
        if distance_to_incident < 5.0:  # Within 5km
            should_reroute = True
            reason = "Accident detected on route"
    elif incident_type == "aqi_spike" and severity in ["high", "critical"]:
        if distance_to_incident < 3.0:  # Within 3km for AQI
            should_reroute = True
            reason = "Hazardous air quality detected on route"
    elif incident_type == "road_closure" and severity in ["high", "critical"]:
        if distance_to_incident < 10.0:  # Within 10km
            should_reroute = True
            reason = "Road closure detected on route"
    elif incident_type == "weather" and severity == "critical":
        if distance_to_incident < 15.0:  # Within 15km for weather
            should_reroute = True
            reason = "Severe weather conditions detected on route"
    
    if should_reroute:
        # Get alternative routes avoiding the incident
        try:
            # For now, we'll return a simple response indicating reroute is needed
            # In a real implementation, this would calculate alternative routes
            return {
                "reroute_needed": True,
                "reason": reason,
                "incident_location": incident_location,
                "incident_type": incident_type,
                "severity": severity,
                "distance_to_incident_km": round(distance_to_incident, 2),
                "recommendation": "Rerouting to safer corridor",
                "alternative_routes": []  # Would be populated in real implementation
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating alternative routes: {str(e)}"
            )
    else:
        return {
            "reroute_needed": False,
            "reason": "Incident not severe enough or too far from route to require rerouting",
            "incident_location": incident_location,
            "incident_type": incident_type,
            "severity": severity,
            "distance_to_incident_km": round(distance_to_incident, 2)
        }


@router.post("/report-incident")
async def report_incident_for_rerouting(
    reporter_id: str,
    incident_type: str,
    location: CoordinatesSchema,
    description: str,
    severity: str = Query("medium", regex="^(low|medium|high|critical)$")
):
    """
    Report an incident that might trigger auto-rerouting for other users
    
    Args:
        reporter_id: ID of user reporting incident
        incident_type: Type of incident
        location: Location of incident
        description: Description of incident
        severity: Severity level
        
    Returns:
        Reported incident details
    """
    # Submit to community service
    report = await community_service.submit_report(
        user_id=reporter_id,
        report_type=incident_type,
        location=location,
        message=description,
        severity=severity
    )
    
    # Check if this incident should trigger alerts for rerouting
    should_alert = severity in ["high", "critical"]
    
    return {
        "report": report,
        "should_trigger_rerouting_alerts": should_alert,
        "report_id": report["report_id"]
    }


@router.get("/high-priority")
async def get_high_priority_incidents(
    center: Optional[CoordinatesSchema] = None,
    hours_back: int = Query(24, ge=1, le=168, description="Hours to look back for incidents")
):
    """
    Get high-priority incidents that might affect many users
    
    Args:
        center: Center coordinates for search (optional)
        hours_back: Hours to look back for incidents
        
    Returns:
        High-priority incidents
    """
    # If no center provided, use Delhi NCR center
    if center is None:
        center = CoordinatesSchema(latitude=28.6139, longitude=77.2090)
    
    # Get recent reports with high trust scores
    reports = await community_service.get_reports_in_area(
        center=center,
        radius_km=20.0,  # Wider radius for high-priority incidents
        min_trust_score=0.7
    )
    
    # Filter for high-priority incidents
    high_priority_incidents = [
        report for report in reports
        if (report["severity"] in ["high", "critical"] or 
            report["trust_score"] > 0.8 or
            report["reports"] > 5)  # Multiple reports indicate importance
    ]
    
    # Sort by priority (severity, trust score, report count)
    high_priority_incidents.sort(
        key=lambda x: (
            {"low": 1, "medium": 2, "high": 3, "critical": 4}[x["severity"]],
            x["trust_score"],
            x["reports"]
        ),
        reverse=True
    )
    
    return {
        "center": center,
        "hours_back": hours_back,
        "high_priority_incidents": high_priority_incidents[:20],  # Limit to top 20
        "total_high_priority": len(high_priority_incidents)
    }


@router.post("/bulk-check")
async def bulk_check_route_safety(
    route_coordinates: List[CoordinatesSchema],
    buffer_distance_meters: float = Query(200.0, ge=50.0, le=1000.0)
):
    """
    Check if a route passes through any known incidents or hazardous areas
    
    Args:
        route_coordinates: List of coordinates along the route
        buffer_distance_meters: Buffer distance around route to check for incidents
        
    Returns:
        Safety assessment for the route
    """
    if len(route_coordinates) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 coordinates required for route analysis"
        )
    
    # Get incidents near the route
    safety_issues = []
    buffer_km = buffer_distance_meters / 1000.0
    
    # Check each point along the route
    check_points = route_coordinates[::max(1, len(route_coordinates) // 10)]  # Sample points
    
    for point in check_points:
        # Get nearby reports
        nearby_reports = await community_service.get_reports_in_area(
            center=point,
            radius_km=buffer_km,
            min_trust_score=0.5
        )
        
        # Filter for active incidents
        active_incidents = [
            report for report in nearby_reports 
            if report["is_active"] and report["severity"] in ["high", "critical"]
        ]
        
        safety_issues.extend(active_incidents)
    
    # Remove duplicates
    unique_issues = []
    seen_ids = set()
    for issue in safety_issues:
        if issue["report_id"] not in seen_ids:
            unique_issues.append(issue)
            seen_ids.add(issue["report_id"])
    
    # Sort by severity
    unique_issues.sort(
        key=lambda x: {"low": 1, "medium": 2, "high": 3, "critical": 4}[x["severity"]],
        reverse=True
    )
    
    is_route_safe = len(unique_issues) == 0
    safety_message = "Route appears safe" if is_route_safe else f"Route has {len(unique_issues)} safety concerns"
    
    return {
        "route_coordinates_count": len(route_coordinates),
        "check_points_sampled": len(check_points),
        "is_route_safe": is_route_safe,
        "safety_message": safety_message,
        "safety_issues": unique_issues[:10],  # Limit to top 10
        "total_safety_issues": len(unique_issues)
    }