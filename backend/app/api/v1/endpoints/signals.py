"""
Traffic signals API endpoints
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.traffic_signal_service import traffic_signal_service
from app.schemas.base import CoordinatesSchema
from app.schemas.route import TrafficSignalState, SignalPrediction, GreenWaveCalculation
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.get("/current/{signal_id}", response_model=TrafficSignalState)
def get_signal_current_state(signal_id: str):
    """Get current state of a specific traffic signal"""
    
    signal_state = traffic_signal_service.get_current_signal_state(signal_id)
    
    if not signal_state:
        raise HTTPException(
            status_code=404,
            detail=f"Traffic signal {signal_id} not found"
        )
    
    return signal_state


@router.post("/predict/{signal_id}", response_model=SignalPrediction)
def predict_signal_state(
    signal_id: str,
    arrival_time: datetime,
    current_speed_kmh: float = Query(..., ge=10, le=100, description="Current vehicle speed in km/h")
):
    """Predict signal state when vehicle arrives"""
    
    # Validate arrival time is in the future
    if arrival_time <= datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Arrival time must be in the future"
        )
    
    # Limit prediction to reasonable timeframe (max 10 minutes)
    max_prediction_time = datetime.utcnow() + timedelta(minutes=10)
    if arrival_time > max_prediction_time:
        raise HTTPException(
            status_code=400,
            detail="Prediction time too far in the future (max 10 minutes)"
        )
    
    prediction = traffic_signal_service.predict_signal_state(
        signal_id=signal_id,
        arrival_time=arrival_time,
        current_speed_kmh=current_speed_kmh
    )
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"Traffic signal {signal_id} not found"
        )
    
    return prediction


@router.post("/nearby", response_model=List[TrafficSignalState])
def get_nearby_signals(
    coordinates: CoordinatesSchema,
    radius_km: float = Query(2.0, ge=0.1, le=10.0, description="Search radius in kilometers")
):
    """Get all traffic signals near a location"""
    
    signals = traffic_signal_service.get_signals_near_location(
        coordinates=coordinates,
        radius_km=radius_km
    )
    
    return signals


@router.post("/along-route", response_model=List[TrafficSignalState])
def get_signals_along_route(
    route_coordinates: List[CoordinatesSchema],
    buffer_meters: float = Query(100.0, ge=50.0, le=500.0, description="Buffer distance from route in meters")
):
    """Get traffic signals along a route"""
    
    if len(route_coordinates) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 coordinates required for route analysis"
        )
    
    signals = traffic_signal_service.get_signals_along_route(
        route_coordinates=route_coordinates,
        buffer_meters=buffer_meters
    )
    
    return signals


@router.get("/green-wave/{corridor_id}", response_model=GreenWaveCalculation)
def calculate_green_wave(
    corridor_id: str,
    average_speed_kmh: float = Query(50.0, ge=20.0, le=80.0, description="Average vehicle speed in km/h")
):
    """Calculate green wave timing for a corridor"""
    
    green_wave = traffic_signal_service.calculate_green_wave_timing(
        corridor_id=corridor_id,
        average_speed_kmh=average_speed_kmh
    )
    
    if not green_wave:
        raise HTTPException(
            status_code=404,
            detail=f"Corridor {corridor_id} not found or has insufficient signals"
        )
    
    return green_wave


@router.post("/optimize-corridor")
def optimize_corridor_timing(
    signal_chain: List[str],
    traffic_density: str = Query("moderate", regex="^(light|moderate|heavy)$", description="Current traffic density")
):
    """Optimize timing for a chain of signals"""
    
    if len(signal_chain) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 signals required for corridor optimization"
        )
    
    if len(signal_chain) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 signals allowed for optimization"
        )
    
    result = traffic_signal_service.optimize_corridor_timing(
        signal_chain=signal_chain,
        traffic_density=traffic_density
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )
    
    return result


@router.post("/adaptive-timing/{signal_id}")
def simulate_adaptive_timing(
    signal_id: str,
    traffic_volume: int = Query(..., ge=0, le=500, description="Current traffic volume (vehicles per hour)"),
    pedestrian_count: int = Query(0, ge=0, le=100, description="Number of pedestrians waiting")
):
    """Simulate adaptive signal timing based on current conditions"""
    
    result = traffic_signal_service.simulate_adaptive_timing(
        signal_id=signal_id,
        traffic_volume=traffic_volume,
        pedestrian_count=pedestrian_count
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )
    
    return result


@router.get("/corridors")
def list_corridors():
    """List all available traffic corridors"""
    
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


@router.get("/corridor-performance/{corridor_id}")
def get_corridor_performance(corridor_id: str):
    """Get performance metrics for a specific corridor"""
    
    performance = traffic_signal_service.get_corridor_performance(corridor_id)
    
    if "error" in performance:
        raise HTTPException(
            status_code=404,
            detail=performance["error"]
        )
    
    return performance


@router.get("/all-signals")
def list_all_signals():
    """List all available traffic signals"""
    
    all_signals = []
    for signal_id in traffic_signal_service.mock_signals.keys():
        signal_state = traffic_signal_service.get_current_signal_state(signal_id)
        if signal_state:
            all_signals.append(signal_state)
    
    return {
        "total_signals": len(all_signals),
        "signals": all_signals
    }


@router.post("/initialize-database")
async def initialize_signal_database(db: Session = Depends(get_db)):
    """Initialize database with mock traffic signal data"""
    
    try:
        await traffic_signal_service.store_signal_data(db)
        
        return {
            "message": "Traffic signal database initialized successfully",
            "signals_created": len(traffic_signal_service.mock_signals),
            "corridors_created": len(traffic_signal_service.corridors)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize database: {str(e)}"
        )


@router.get("/signal-info/{signal_id}")
def get_signal_detailed_info(signal_id: str):
    """Get detailed information about a specific signal"""
    
    if signal_id not in traffic_signal_service.mock_signals:
        raise HTTPException(
            status_code=404,
            detail=f"Traffic signal {signal_id} not found"
        )
    
    signal_data = traffic_signal_service.mock_signals[signal_id]
    current_state = traffic_signal_service.get_current_signal_state(signal_id)
    
    return {
        "signal_id": signal_id,
        "coordinates": signal_data["coordinates"],
        "road_type": signal_data["road_type"],
        "timing": {
            "cycle_time_seconds": signal_data["cycle_time_seconds"],
            "green_duration": signal_data["green_duration"],
            "yellow_duration": signal_data["yellow_duration"],
            "red_duration": signal_data["red_duration"],
            "offset_seconds": signal_data["offset_seconds"]
        },
        "coordination": {
            "is_coordinated": signal_data["is_coordinated"],
            "corridor_id": signal_data["corridor_id"]
        },
        "features": {
            "adaptive": signal_data["adaptive"],
            "pedestrian_crossing": signal_data["pedestrian_crossing"]
        },
        "current_state": current_state,
        "last_updated": signal_data["last_updated"]
    }


@router.post("/bulk-predict")
def bulk_predict_signals(
    signal_predictions: List[dict],
    current_speed_kmh: float = Query(50.0, ge=10, le=100)
):
    """Predict states for multiple signals at once"""
    
    if len(signal_predictions) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 signal predictions allowed per request"
        )
    
    results = []
    
    for pred_request in signal_predictions:
        try:
            signal_id = pred_request["signal_id"]
            arrival_time = datetime.fromisoformat(pred_request["arrival_time"])
            
            prediction = traffic_signal_service.predict_signal_state(
                signal_id=signal_id,
                arrival_time=arrival_time,
                current_speed_kmh=current_speed_kmh
            )
            
            if prediction:
                results.append({
                    "signal_id": signal_id,
                    "prediction": prediction,
                    "status": "success"
                })
            else:
                results.append({
                    "signal_id": signal_id,
                    "prediction": None,
                    "status": "not_found"
                })
                
        except Exception as e:
            results.append({
                "signal_id": pred_request.get("signal_id", "unknown"),
                "prediction": None,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_requests": len(signal_predictions),
        "successful_predictions": len([r for r in results if r["status"] == "success"]),
        "results": results
    }


# Green Wave Endpoints
@router.post("/green-wave/calculate-offset")
def calculate_green_wave_offset(
    distance_meters: float = Query(..., ge=50, le=5000, description="Distance between signals in meters"),
    average_speed_kmh: float = Query(..., ge=20, le=80, description="Average vehicle speed"),
    signal_cycle_time: int = Query(120, ge=60, le=300, description="Signal cycle time in seconds")
):
    """Calculate optimal signal offset for green wave coordination"""
    
    from app.services.green_wave_service import green_wave_service
    
    offset = green_wave_service.calculate_green_wave_offset(
        distance_meters=distance_meters,
        average_speed_kmh=average_speed_kmh,
        signal_cycle_time=signal_cycle_time
    )
    
    return {
        "distance_meters": distance_meters,
        "average_speed_kmh": average_speed_kmh,
        "signal_cycle_time": signal_cycle_time,
        "recommended_offset_seconds": offset,
        "travel_time_seconds": distance_meters / (average_speed_kmh / 3.6)
    }


@router.post("/green-wave/optimize-corridor")
def optimize_green_wave_corridor(
    signal_chain: List[str],
    target_speed_kmh: float = Query(50.0, ge=30, le=70, description="Target travel speed"),
    traffic_density: str = Query("moderate", regex="^(light|moderate|heavy)$")
):
    """Optimize green wave timing for entire corridor"""
    
    from app.services.green_wave_service import green_wave_service
    
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


@router.post("/green-wave/simulate")
def simulate_green_wave_progression(
    corridor_id: str,
    vehicle_speed_kmh: float = Query(..., ge=20, le=80, description="Vehicle travel speed"),
    start_time: Optional[datetime] = None
):
    """Simulate vehicle progression through green wave"""
    
    from app.services.green_wave_service import green_wave_service
    
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


@router.post("/green-wave/bandwidth-analysis")
def analyze_green_wave_bandwidth(
    signal_chain: List[str],
    min_speed_kmh: float = Query(40, ge=20, le=60, description="Minimum analysis speed"),
    max_speed_kmh: float = Query(60, ge=40, le=80, description="Maximum analysis speed")
):
    """Analyze green wave bandwidth efficiency"""
    
    from app.services.green_wave_service import green_wave_service
    
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