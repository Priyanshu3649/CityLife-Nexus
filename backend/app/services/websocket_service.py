"""
WebSocket service for real-time communication
Handles live route updates, emergency alerts, and traffic signal updates
"""
import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import logging
from fastapi import WebSocket
import uuid

from app.schemas.base import CoordinatesSchema
from app.schemas.route import TrafficSignalState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        # Active connections grouped by type
        self.connections: Dict[str, Set[WebSocket]] = {
            "route_updates": set(),
            "emergency_alerts": set(),
            "traffic_signals": set(),
            "aqi_updates": set()
        }
        
        # User location tracking for geospatial alerts
        self.user_locations: Dict[WebSocket, CoordinatesSchema] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, connection_type: str = "general"):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        if connection_type not in self.connections:
            self.connections[connection_type] = set()
        
        self.connections[connection_type].add(websocket)
        
        # Initialize metadata
        self.connection_metadata[websocket] = {
            "connected_at": datetime.utcnow(),
            "connection_id": str(uuid.uuid4()),
            "type": connection_type,
            "last_ping": datetime.utcnow()
        }
        
        logger.info(f"New {connection_type} connection: {len(self.connections[connection_type])} total")
        
        # Send welcome message
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "connection_id": self.connection_metadata[websocket]["connection_id"],
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        # Remove from all connection groups
        for connection_type, connections in self.connections.items():
            connections.discard(websocket)
        
        # Clean up metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        # Clean up location tracking
        if websocket in self.user_locations:
            del self.user_locations[websocket]
        
        logger.info("WebSocket connection closed")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to connection: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_type(self, message: dict, connection_type: str):
        """Broadcast message to all connections of specific type"""
        if connection_type not in self.connections:
            return
        
        disconnected = []
        
        for websocket in self.connections[connection_type].copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_type}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_geospatial_alert(
        self, 
        message: dict, 
        center: CoordinatesSchema, 
        radius_km: float
    ):
        """Broadcast emergency alert to users within geographic radius"""
        affected_connections = []
        
        for websocket, user_location in self.user_locations.items():
            distance = self._calculate_distance(center, user_location)
            if distance <= radius_km:
                affected_connections.append(websocket)
        
        # Send to affected users
        for websocket in affected_connections:
            try:
                await websocket.send_text(json.dumps({
                    **message,
                    "distance_from_incident": self._calculate_distance(
                        center, self.user_locations[websocket]
                    )
                }))
            except Exception as e:
                logger.error(f"Failed to send geospatial alert: {e}")
                self.disconnect(websocket)
        
        logger.info(f"Geospatial alert sent to {len(affected_connections)} users")
    
    def update_user_location(self, websocket: WebSocket, location: CoordinatesSchema):
        """Update user's current location for geospatial alerts"""
        self.user_locations[websocket] = location
        
        # Update last seen timestamp
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["last_location_update"] = datetime.utcnow()
    
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
    
    async def send_heartbeat(self):
        """Send heartbeat to all connections to keep them alive"""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        all_connections = set()
        for connections in self.connections.values():
            all_connections.update(connections)
        
        for websocket in list(all_connections):
            try:
                await websocket.send_text(json.dumps(heartbeat_message))
                # Update last ping time
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_ping"] = datetime.utcnow()
            except Exception as e:
                logger.error(f"Heartbeat failed for connection: {e}")
                self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, int]:
        """Get statistics about active connections"""
        return {
            connection_type: len(connections)
            for connection_type, connections in self.connections.items()
        }


class WebSocketService:
    """Main WebSocket service for real-time features"""
    
    def __init__(self):
        self.manager = ConnectionManager()
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def start_heartbeat(self):
        """Start periodic heartbeat task"""
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self):
        """Periodic heartbeat to keep connections alive"""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                await self.manager.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
    
    async def handle_route_updates(self, websocket: WebSocket):
        """Handle route update WebSocket connection"""
        await self.manager.connect(websocket, "route_updates")
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "location_update":
                    location = CoordinatesSchema(**message["location"])
                    self.manager.update_user_location(websocket, location)
                    
                elif message.get("type") == "request_route_update":
                    # Handle route update request
                    await self._handle_route_update_request(websocket, message)
                
        except Exception as e:
            logger.error(f"Route updates WebSocket error: {e}")
        finally:
            self.manager.disconnect(websocket)
    
    async def handle_emergency_alerts(self, websocket: WebSocket):
        """Handle emergency alert WebSocket connection"""
        await self.manager.connect(websocket, "emergency_alerts")
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "location_update":
                    location = CoordinatesSchema(**message["location"])
                    self.manager.update_user_location(websocket, location)
                    
                elif message.get("type") == "report_incident":
                    # Handle community incident reporting
                    await self._handle_incident_report(websocket, message)
                
        except Exception as e:
            logger.error(f"Emergency alerts WebSocket error: {e}")
        finally:
            self.manager.disconnect(websocket)
    
    async def handle_traffic_signals(self, websocket: WebSocket):
        """Handle traffic signal update WebSocket connection"""
        await self.manager.connect(websocket, "traffic_signals")
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "subscribe_signals":
                    # Handle signal subscription for specific area
                    await self._handle_signal_subscription(websocket, message)
                
        except Exception as e:
            logger.error(f"Traffic signals WebSocket error: {e}")
        finally:
            self.manager.disconnect(websocket)
    
    async def broadcast_emergency_alert(self, alert: Dict[str, Any]):
        """Broadcast emergency alert to affected users"""
        alert_message = {
            "type": "emergency_alert",
            "alert": alert,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send geospatial alert to users in affected area
        if "latitude" in alert and "longitude" in alert:
            center = CoordinatesSchema(latitude=float(alert["latitude"]), longitude=float(alert["longitude"]))
            radius_km = float(alert.get("radius_km", 5.0))
            await self.manager.broadcast_geospatial_alert(
                alert_message, center, radius_km
            )
        
        # Also broadcast to all emergency alert subscribers
        await self.manager.broadcast_to_type(alert_message, "emergency_alerts")
    
    async def broadcast_traffic_signal_update(self, signal_state: TrafficSignalState):
        """Broadcast traffic signal state update"""
        signal_message = {
            "type": "traffic_signal_update",
            "signal": {
                "signal_id": signal_state.signal_id,
                "coordinates": {
                    "latitude": signal_state.coordinates.latitude,
                    "longitude": signal_state.coordinates.longitude
                },
                "current_state": signal_state.current_state,
                "cycle_time_seconds": signal_state.cycle_time_seconds,
                "time_to_next_change": signal_state.time_to_next_change,
                "is_coordinated": signal_state.is_coordinated
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.broadcast_to_type(signal_message, "traffic_signals")
    
    async def broadcast_aqi_update(self, location: CoordinatesSchema, aqi_value: int, pollutants: dict):
        """Broadcast AQI update for a location"""
        aqi_message = {
            "type": "aqi_update",
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "aqi_value": aqi_value,
            "pollutants": pollutants,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.broadcast_to_type(aqi_message, "aqi_updates")
    
    async def _handle_route_update_request(self, websocket: WebSocket, message: dict):
        """Handle route update request from client"""
        try:
            # This would integrate with the route optimizer
            response = {
                "type": "route_update_response",
                "request_id": message.get("request_id"),
                "status": "processing",
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.manager.send_personal_message(websocket, response)
        except Exception as e:
            logger.error(f"Route update request handling failed: {e}")
    
    async def _handle_incident_report(self, websocket: WebSocket, message: dict):
        """Handle community incident report"""
        try:
            # Validate and process incident report
            incident_data = message.get("incident", {})
            
            # Create incident report (this would integrate with emergency service)
            response = {
                "type": "incident_report_response",
                "report_id": str(uuid.uuid4()),
                "status": "received",
                "message": "Thank you for the report. We're verifying the incident.",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.manager.send_personal_message(websocket, response)
            
            # Broadcast incident alert to nearby users
            if "location" in incident_data:
                alert_message = {
                    "type": "community_incident_alert",
                    "incident": incident_data,
                    "source": "community_report",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                location = CoordinatesSchema(**incident_data["location"])
                await self.manager.broadcast_geospatial_alert(
                    alert_message, location, 5.0  # 5km radius
                )
                
        except Exception as e:
            logger.error(f"Incident report handling failed: {e}")
    
    async def _handle_signal_subscription(self, websocket: WebSocket, message: dict):
        """Handle traffic signal subscription for area"""
        try:
            # This would integrate with traffic signal service
            response = {
                "type": "signal_subscription_response",
                "status": "subscribed",
                "area": message.get("area"),
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.manager.send_personal_message(websocket, response)
        except Exception as e:
            logger.error(f"Signal subscription handling failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket service statistics"""
        return {
            "active_connections": self.manager.get_connection_stats(),
            "total_connections": sum(self.manager.get_connection_stats().values()),
            "heartbeat_active": self.heartbeat_task is not None and not self.heartbeat_task.done(),
            "last_update": datetime.utcnow().isoformat()
        }


# Global instance
websocket_service = WebSocketService()