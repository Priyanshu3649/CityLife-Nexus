"""
Green Wave Synchronization API endpoints
"""
from typing import List, Optional, Tuple
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.green_wave_service import green_wave_service
from app.services.traffic_signal_service import traffic_signal_service
from app.schemas.base import CoordinatesSchema
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.post("/calculate-offset")
async def calculate_green_wave_offset(
    distance_meters: float = Query(..., ge=50, le=5000, description="Distance between signals in meters"),
    average_speed_kmh: float = Query(..., ge=20, le=80, description="Average vehicle speed"),
    signal_cycle_time: int = Query(120, ge=60, le=300, description="Signal cycle time in seconds")
):
    """
    Calculate optimal signal offset for green wave coordination
    
    Args:
        distance_meters: Distance between two traffic signals
        average_speed_kmh: Average vehicle speed on this road
        signal_cycle_time: Signal cycle time in seconds
        
    Returns:
        Recommended offset for green wave coordination
    """
    offset = green_wave_service.calculate_green_wave_offset(
        distance_meters=distance_meters,
        average_speed_kmh=average_speed_kmh,
        signal_cycle_time=signal_cycle_time
    )
    
    travel_time_seconds = distance_meters / (average_speed_kmh / 3.6)
    
    return {
        "distance_meters": distance_meters,
        "average_speed_kmh": average_speed_kmh,
        "signal_cycle_time": signal_cycle_time,
        "recommended_offset_seconds": offset,
        "travel_time_seconds": travel_time_seconds,
        "offset_efficiency": min(1.0, travel_time_seconds / signal_cycle_time)
    }


@router.post("/optimize-corridor")
async def optimize_green_wave_corridor(
    signal_chain: List[str],
    target_speed_kmh: float = Query(50.0, ge=30, le=70, description="Target travel speed"),
    traffic_density: str = Query("moderate", regex="^(light|moderate|heavy)$")
):
    """
    Optimize green wave timing for entire corridor
    
    Args:
        signal_chain: List of signal IDs in sequence
        target_speed_kmh: Desired travel speed
        traffic_density: Current traffic conditions
        
    Returns:
        Optimization results with timing recommendations
    """
    if len(signal_chain) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 signals required for corridor optimization"
        )
    
    if len(signal_chain) > 15:
        raise HTTPException(
            status_code=400,
            detail="Maximum 15 signals allowed for corridor optimization"
        )
    
    result = green_wave_service.optimize_corridor_timing(
        signal_chain=signal_chain,
        target_speed_kmh=target_speed_kmh,
        traffic_density=traffic_density
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )
    
    return result


@router.post("/simulate-progression")
async def simulate_green_wave_progression(
    corridor_id: str,
    vehicle_speed_kmh: float = Query(..., ge=20, le=80, description="Vehicle travel speed"),
    start_time: Optional[datetime] = None
):
    """
    Simulate vehicle progression through green wave
    
    Args:
        corridor_id: ID of the corridor to simulate
        vehicle_speed_kmh: Vehicle travel speed
        start_time: Simulation start time (defaults to current time)
        
    Returns:
        Simulation results with signal encounters
    """
    if start_time is None:
        start_time = datetime.utcnow()
    
    result = green_wave_service.simulate_green_wave_progression(
        corridor_id=corridor_id,
        vehicle_speed_kmh=vehicle_speed_kmh,
        start_time=start_time
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )
    
    return result


@router.post("/bandwidth-analysis")
async def analyze_green_wave_bandwidth(
    signal_chain: List[str],
    min_speed_kmh: float = Query(40, ge=20, le=60, description="Minimum analysis speed"),
    max_speed_kmh: float = Query(60, ge=40, le=80, description="Maximum analysis speed")
):
    """
    Analyze green wave bandwidth efficiency
    
    Args:
        signal_chain: List of signal IDs
        min_speed_kmh: Minimum analysis speed
        max_speed_kmh: Maximum analysis speed
        
    Returns:
        Bandwidth analysis results
    """
    if len(signal_chain) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 signals required for bandwidth analysis"
        )
    
    if min_speed_kmh >= max_speed_kmh:
        raise HTTPException(
            status_code=400,
            detail="Minimum speed must be less than maximum speed"
        )
    
    result = green_wave_service.calculate_bandwidth_efficiency(
        signal_chain=signal_chain,
        speed_range=(min_speed_kmh, max_speed_kmh)
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )
    
    return result


@router.get("/corridors")
async def list_available_corridors():
    """
    List all available traffic corridors for green wave coordination
    
    Returns:
        List of available corridors
    """
    corridors = []
    for corridor_id, signal_ids in traffic_signal_service.corridors.items():
        corridor_info = {
            "corridor_id": corridor_id,
            "signal_count": len(signal_ids),
            "signal_ids": signal_ids,
            "performance": traffic_signal_service.get_corridor_performance(corridor_id)
        }
        corridors.append(corridor_info)
    
    return {
        "total_corridors": len(corridors),
        "corridors": corridors
    }


@router.get("/corridor/{corridor_id}/performance")
async def get_corridor_performance(corridor_id: str):
    """
    Get performance metrics for a specific corridor
    
    Args:
        corridor_id: ID of the corridor
        
    Returns:
        Performance metrics for the corridor
    """
    performance = traffic_signal_service.get_corridor_performance(corridor_id)
    
    if "error" in performance:
        raise HTTPException(
            status_code=404,
            detail=performance["error"]
        )
    
    return performance


@router.post("/bulk-optimize")
async def bulk_optimize_multiple_corridors(
    optimization_requests: List[dict]
):
    """
    Optimize multiple corridors at once
    
    Args:
        optimization_requests: List of optimization request data
        
    Returns:
        Optimization results for all corridors
    """
    if not optimization_requests:
        raise HTTPException(
            status_code=400,
            detail="At least one optimization request required"
        )
    
    if len(optimization_requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 optimization requests allowed per bulk operation"
        )
    
    results = []
    
    for request_data in optimization_requests:
        try:
            signal_chain = request_data["signal_chain"]
            target_speed_kmh = request_data.get("target_speed_kmh", 50.0)
            traffic_density = request_data.get("traffic_density", "moderate")
            
            result = green_wave_service.optimize_corridor_timing(
                signal_chain=signal_chain,
                target_speed_kmh=target_speed_kmh,
                traffic_density=traffic_density
            )
            
            results.append({
                "signal_chain": signal_chain,
                "result": result,
                "status": "success" if "error" not in result else "error"
            })
            
        except Exception as e:
            results.append({
                "signal_chain": request_data.get("signal_chain", []),
                "result": {"error": str(e)},
                "status": "error"
            })
    
    successful_optimizations = sum(1 for r in results if r["status"] == "success")
    
    return {
        "total_requests": len(optimization_requests),
        "successful_optimizations": successful_optimizations,
        "results": results
    }