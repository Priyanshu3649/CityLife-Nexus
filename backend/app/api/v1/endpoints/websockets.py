"""
WebSocket API endpoints for real-time communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from app.services.websocket_service import websocket_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/route-updates")
async def websocket_route_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time route updates
    
    Client can send:
    - location_update: Update current location
    - request_route_update: Request new route calculation
    
    Server sends:
    - route_update: New optimized route
    - aqi_alert: Air quality alerts along route
    - traffic_update: Traffic condition changes
    """
    try:
        await websocket_service.handle_route_updates(websocket)
    except WebSocketDisconnect:
        logger.info("Route updates WebSocket disconnected")
    except Exception as e:
        logger.error(f"Route updates WebSocket error: {e}")


@router.websocket("/emergency-alerts")
async def websocket_emergency_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for emergency alerts and community reporting
    
    Client can send:
    - location_update: Update current location for geospatial alerts
    - report_incident: Report emergency/incident
    
    Server sends:
    - emergency_alert: City-wide emergency broadcasts
    - community_incident_alert: Community-reported incidents
    - incident_report_response: Confirmation of submitted reports
    """
    try:
        await websocket_service.handle_emergency_alerts(websocket)
    except WebSocketDisconnect:
        logger.info("Emergency alerts WebSocket disconnected")
    except Exception as e:
        logger.error(f"Emergency alerts WebSocket error: {e}")


@router.websocket("/traffic-signals")
async def websocket_traffic_signals(websocket: WebSocket):
    """
    WebSocket endpoint for real-time traffic signal updates
    
    Client can send:
    - subscribe_signals: Subscribe to signals in specific area
    - location_update: Update location for nearby signals
    
    Server sends:
    - traffic_signal_update: Signal state changes
    - green_wave_update: Coordinated signal timing updates
    - signal_prediction: Upcoming signal state predictions
    """
    try:
        await websocket_service.handle_traffic_signals(websocket)
    except WebSocketDisconnect:
        logger.info("Traffic signals WebSocket disconnected")
    except Exception as e:
        logger.error(f"Traffic signals WebSocket error: {e}")


@router.websocket("/aqi-updates")
async def websocket_aqi_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time air quality updates
    
    Client can send:
    - location_update: Update location for local AQI
    - subscribe_area: Subscribe to AQI updates for area
    
    Server sends:
    - aqi_update: New air quality readings
    - pollution_alert: High pollution warnings
    - health_advisory: Health impact notifications
    """
    await websocket.accept()
    
    # Add to AQI updates connection group
    websocket_service.manager.connections["aqi_updates"].add(websocket)
    websocket_service.manager.connection_metadata[websocket] = {
        "connected_at": websocket_service.manager.connection_metadata.get(websocket, {}).get("connected_at"),
        "connection_id": websocket_service.manager.connection_metadata.get(websocket, {}).get("connection_id"),
        "type": "aqi_updates"
    }
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle AQI-specific messages here
            logger.info(f"Received AQI message: {data}")
            
    except WebSocketDisconnect:
        logger.info("AQI updates WebSocket disconnected")
    except Exception as e:
        logger.error(f"AQI updates WebSocket error: {e}")
    finally:
        websocket_service.manager.disconnect(websocket)


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_service.get_stats()