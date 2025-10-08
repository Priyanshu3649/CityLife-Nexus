"""
Data interpolation API endpoints for filling data gaps
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.interpolation_service import interpolation_service
from app.schemas.base import CoordinatesSchema
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.post("/idw-interpolation")
async def perform_idw_interpolation(
    target_point: CoordinatesSchema,
    known_points: List[Dict[str, Any]],
    power: float = Query(2.0, ge=0.1, le=5.0, description="Power parameter for IDW")
):
    """
    Perform Inverse Distance Weighting interpolation
    
    Args:
        target_point: Point where value needs to be estimated
        known_points: List of {"coordinates": {"latitude": float, "longitude": float}, "value": float} dictionaries
        power: Power parameter for IDW
        
    Returns:
        Interpolated value at target point
    """
    if not known_points:
        raise HTTPException(
            status_code=400,
            detail="At least one known point required"
        )
    
    # Convert known points to the format expected by the service
    converted_points = []
    for point_data in known_points:
        try:
            coords = CoordinatesSchema(
                latitude=point_data["coordinates"]["latitude"],
                longitude=point_data["coordinates"]["longitude"]
            )
            value = point_data["value"]
            converted_points.append((coords, value))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid known point format: {str(e)}"
            )
    
    interpolated_value = interpolation_service.idw_interpolation(
        target_point=target_point,
        known_points=converted_points,
        power=power
    )
    
    return {
        "target_point": target_point,
        "interpolated_value": interpolated_value,
        "method": "IDW",
        "power": power
    }


@router.post("/linear-interpolation")
async def perform_linear_interpolation(
    x: float,
    x1: float,
    x2: float,
    y1: float,
    y2: float
):
    """
    Perform linear interpolation between two points
    
    Args:
        x: Target x value
        x1, x2: Known x values
        y1, y2: Known y values
        
    Returns:
        Interpolated y value
    """
    if x2 == x1:
        raise HTTPException(
            status_code=400,
            detail="x1 and x2 cannot be equal"
        )
    
    interpolated_value = interpolation_service.linear_interpolation(x, x1, x2, y1, y2)
    
    return {
        "x": x,
        "x1": x1,
        "x2": x2,
        "y1": y1,
        "y2": y2,
        "interpolated_y": interpolated_value,
        "method": "Linear"
    }


@router.post("/temporal-interpolation")
async def perform_temporal_interpolation(
    target_time: datetime,
    time1: datetime,
    time2: datetime,
    value1: float,
    value2: float
):
    """
    Perform temporal interpolation between two time points
    
    Args:
        target_time: Target time for interpolation
        time1, time2: Known time points
        value1, value2: Values at known time points
        
    Returns:
        Interpolated value at target time
    """
    if time2 == time1:
        raise HTTPException(
            status_code=400,
            detail="time1 and time2 cannot be equal"
        )
    
    interpolated_value = interpolation_service.temporal_interpolation(
        target_time, time1, time2, value1, value2
    )
    
    return {
        "target_time": target_time,
        "time1": time1,
        "time2": time2,
        "value1": value1,
        "value2": value2,
        "interpolated_value": interpolated_value,
        "method": "Temporal"
    }


@router.post("/aqi-along-route")
async def interpolate_aqi_along_route(
    route_waypoints: List[CoordinatesSchema],
    aqi_readings: List[Dict[str, Any]]
):
    """
    Interpolate AQI values along a route
    
    Args:
        route_waypoints: List of coordinates along the route
        aqi_readings: List of {"coordinates": {"latitude": float, "longitude": float}, "aqi_value": float} dictionaries
        
    Returns:
        List of interpolated AQI values for each waypoint
    """
    if not route_waypoints:
        raise HTTPException(
            status_code=400,
            detail="At least one route waypoint required"
        )
    
    # Convert AQI readings to the format expected by the service
    converted_readings = []
    for reading_data in aqi_readings:
        try:
            coords = CoordinatesSchema(
                latitude=reading_data["coordinates"]["latitude"],
                longitude=reading_data["coordinates"]["longitude"]
            )
            aqi_value = reading_data["aqi_value"]
            converted_readings.append((coords, aqi_value))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid AQI reading format: {str(e)}"
            )
    
    interpolated_aqi = interpolation_service.interpolate_aqi_along_route(
        route_waypoints=route_waypoints,
        aqi_readings=converted_readings
    )
    
    return {
        "route_waypoints": len(route_waypoints),
        "aqi_readings_used": len(converted_readings),
        "interpolated_aqi_values": interpolated_aqi
    }


@router.post("/signal-timing")
async def interpolate_signal_timing(
    target_signal: CoordinatesSchema,
    known_signals: List[Dict[str, Any]]
):
    """
    Interpolate signal timing data for a target signal
    
    Args:
        target_signal: Coordinates of signal to estimate
        known_signals: List of {"coordinates": {"latitude": float, "longitude": float}, "timing_data": dict} dictionaries
        
    Returns:
        Interpolated signal timing data
    """
    # Convert known signals to the format expected by the service
    converted_signals = []
    for signal_data in known_signals:
        try:
            coords = CoordinatesSchema(
                latitude=signal_data["coordinates"]["latitude"],
                longitude=signal_data["coordinates"]["longitude"]
            )
            timing_data = signal_data["timing_data"]
            converted_signals.append((coords, timing_data))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid signal data format: {str(e)}"
            )
    
    interpolated_timing = interpolation_service.interpolate_signal_timing(
        target_signal=target_signal,
        known_signals=converted_signals
    )
    
    return {
        "target_signal": target_signal,
        "interpolated_timing": interpolated_timing,
        "known_signals_used": len(converted_signals)
    }


@router.post("/smooth-time-series")
async def smooth_time_series_data(
    data_points: List[Dict[str, Any]],
    window_size: int = Query(5, ge=3, le=21, description="Size of moving average window")
):
    """
    Apply moving average smoothing to time series data
    
    Args:
        data_points: List of {"timestamp": datetime, "value": float} dictionaries
        window_size: Size of moving average window
        
    Returns:
        Smoothed data points
    """
    if not data_points:
        raise HTTPException(
            status_code=400,
            detail="At least one data point required"
        )
    
    # Convert data points to the format expected by the service
    converted_points = []
    for point_data in data_points:
        try:
            timestamp = datetime.fromisoformat(point_data["timestamp"].replace('Z', '+00:00'))
            value = point_data["value"]
            converted_points.append((timestamp, value))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data point format: {str(e)}"
            )
    
    smoothed_points = interpolation_service.smooth_time_series(
        data_points=converted_points,
        window_size=window_size
    )
    
    # Convert back to serializable format
    result_points = [
        {
            "timestamp": point[0].isoformat(),
            "value": point[1]
        }
        for point in smoothed_points
    ]
    
    return {
        "original_points": len(data_points),
        "smoothed_points": result_points,
        "window_size": window_size,
        "method": "Moving Average"
    }


@router.post("/fill-missing-data")
async def fill_missing_data_points(
    data_points: List[Optional[float]],
    method: str = Query("linear", regex="^(linear|previous|next)$")
):
    """
    Fill missing data points in a series
    
    Args:
        data_points: List of values with None for missing data
        method: Interpolation method (linear, previous, next)
        
    Returns:
        List with missing data filled
    """
    if not data_points:
        raise HTTPException(
            status_code=400,
            detail="At least one data point required"
        )
    
    filled_data = interpolation_service.fill_missing_data(
        data_points=data_points,
        method=method
    )
    
    return {
        "original_points": len(data_points),
        "filled_points": filled_data,
        "missing_points_filled": len([p for p in data_points if p is None]),
        "method": method
    }