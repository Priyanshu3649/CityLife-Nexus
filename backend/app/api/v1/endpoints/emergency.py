"""
Emergency alerts API endpoints
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class EmergencyAlert(BaseModel):
    id: str
    title: str
    description: str
    severity: str  # low, medium, high, critical
    category: str  # traffic, weather, accident, road_closure, construction
    location: dict  # {"latitude": float, "longitude": float}
    affected_radius_km: float
    start_time: datetime
    end_time: Optional[datetime]
    recommended_action: str
    created_at: datetime


class EmergencyAlertResponse(BaseModel):
    alerts: List[EmergencyAlert]
    total_count: int


# Mock emergency alerts data for demonstration
MOCK_EMERGENCY_ALERTS = [
    {
        "id": "alert_001",
        "title": "Road Closure - Connaught Place",
        "description": "Inner Circle road closed due to construction work. Expect delays of 15-20 minutes.",
        "severity": "medium",
        "category": "road_closure",
        "location": {"latitude": 28.6304, "longitude": 77.2177},
        "affected_radius_km": 0.5,
        "start_time": datetime.utcnow() - timedelta(hours=2),
        "end_time": datetime.utcnow() + timedelta(hours=4),
        "recommended_action": "Use alternate route via Janpath or Sansad Marg",
        "created_at": datetime.utcnow() - timedelta(hours=3)
    },
    {
        "id": "alert_002",
        "title": "Traffic Accident - ITO",
        "description": "Multi-vehicle accident on ITO flyover. Emergency services on site.",
        "severity": "high",
        "category": "accident",
        "location": {"latitude": 28.6280, "longitude": 77.2410},
        "affected_radius_km": 1.0,
        "start_time": datetime.utcnow() - timedelta(minutes=30),
        "end_time": None,
        "recommended_action": "Avoid area if possible. Expect delays of 20-30 minutes.",
        "created_at": datetime.utcnow() - timedelta(minutes=35)
    },
    {
        "id": "alert_003",
        "title": "Heavy Rainfall Warning",
        "description": "Heavy rainfall expected in next 2 hours. Visibility may be reduced.",
        "severity": "medium",
        "category": "weather",
        "location": {"latitude": 28.6139, "longitude": 77.2090},
        "affected_radius_km": 10.0,
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow() + timedelta(hours=2),
        "recommended_action": "Reduce speed and maintain safe distance from other vehicles",
        "created_at": datetime.utcnow() - timedelta(minutes=10)
    }
]


@router.get("/", response_model=EmergencyAlertResponse)
def get_emergency_alerts(
    latitude: Optional[float] = Query(None, description="Latitude for location-based alerts"),
    longitude: Optional[float] = Query(None, description="Longitude for location-based alerts"),
    radius_km: float = Query(5.0, ge=0.1, le=50.0, description="Search radius in kilometers"),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$", description="Filter by severity level"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get active emergency alerts
    """
    try:
        # Filter alerts based on parameters
        active_alerts = []
        current_time = datetime.utcnow()
        
        for alert_data in MOCK_EMERGENCY_ALERTS:
            alert = EmergencyAlert(**alert_data)
            
            # Check if alert is currently active
            if alert.start_time <= current_time and (alert.end_time is None or alert.end_time > current_time):
                # Filter by severity if specified
                if severity and alert.severity != severity:
                    continue
                    
                # Filter by category if specified
                if category and alert.category != category:
                    continue
                
                # Filter by location if specified
                if latitude is not None and longitude is not None:
                    # Calculate distance between alert location and requested location
                    distance = _calculate_distance(
                        {"latitude": latitude, "longitude": longitude},
                        alert.location
                    )
                    if distance > radius_km:
                        continue
                
                active_alerts.append(alert)
        
        return EmergencyAlertResponse(
            alerts=active_alerts,
            total_count=len(active_alerts)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve emergency alerts: {str(e)}")


@router.get("/{alert_id}", response_model=EmergencyAlert)
def get_emergency_alert(alert_id: str):
    """
    Get specific emergency alert by ID
    """
    try:
        for alert_data in MOCK_EMERGENCY_ALERTS:
            if alert_data["id"] == alert_id:
                # Check if alert is currently active
                current_time = datetime.utcnow()
                alert = EmergencyAlert(**alert_data)
                if alert.start_time <= current_time and (alert.end_time is None or alert.end_time > current_time):
                    return alert
                else:
                    raise HTTPException(status_code=404, detail="Alert not found or no longer active")
        
        raise HTTPException(status_code=404, detail="Alert not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve emergency alert: {str(e)}")


def _calculate_distance(coord1: dict, coord2: dict) -> float:
    """
    Calculate distance between two coordinates in kilometers using Haversine formula
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [
        coord1["latitude"], coord1["longitude"],
        coord2["latitude"], coord2["longitude"]
    ])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r