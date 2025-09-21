"""
Main API router for SafeAir Navigator
"""
from fastapi import APIRouter

from app.api.v1.endpoints import sessions, routes, signals, aqi, emergency, analytics

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(signals.router, prefix="/signals", tags=["traffic-signals"])
api_router.include_router(aqi.router, prefix="/aqi", tags=["air-quality"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["emergency"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])