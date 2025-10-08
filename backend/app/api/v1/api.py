"""
Main API router for CityLife Nexus
"""
from fastapi import APIRouter

from app.api.v1.endpoints import sessions, routes, signals, aqi, emergency, analytics, health_impact, maps, websockets, traffic_predictor, parking, eco_score, community, interpolation, green_wave, incidents

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(signals.router, prefix="/signals", tags=["traffic-signals"])
api_router.include_router(aqi.router, prefix="/aqi", tags=["air-quality"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["emergency"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(health_impact.router, prefix="/health-impact", tags=["health-impact"])
api_router.include_router(maps.router, prefix="/maps", tags=["google-maps"])
api_router.include_router(websockets.router, prefix="/ws", tags=["websockets"])
api_router.include_router(traffic_predictor.router, prefix="/traffic-predictor", tags=["traffic-predictor"])
api_router.include_router(parking.router, prefix="/parking", tags=["parking"])
api_router.include_router(eco_score.router, prefix="/eco-score", tags=["eco-score"])
api_router.include_router(community.router, prefix="/community", tags=["community"])
api_router.include_router(interpolation.router, prefix="/interpolation", tags=["interpolation"])
api_router.include_router(green_wave.router, prefix="/green-wave", tags=["green-wave"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
