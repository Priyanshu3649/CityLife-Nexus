"""
Session management API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_session, get_session_service
from app.services.session_service import SessionService, generate_session_id
from app.schemas.user import (
    UserSessionCreate,
    UserSessionUpdate,
    UserSessionResponse,
    UserPreferences,
    HealthProfile
)

router = APIRouter()


@router.post("/create", response_model=UserSessionResponse)
def create_session(
    session_data: Optional[UserSessionCreate] = None,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Create a new user session
    If no session_data provided, creates session with auto-generated ID
    """
    if not session_data:
        # Auto-generate session ID if not provided
        session_id = generate_session_id()
        session_data = UserSessionCreate(
            session_id=session_id,
            vehicle_type="car"
        )
    
    try:
        return session_service.create_session(session_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserSessionResponse)
def get_current_session_info(
    current_session: UserSessionResponse = Depends(get_current_session)
):
    """Get current session information"""
    return current_session


@router.get("/{session_id}", response_model=UserSessionResponse)
def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get session by ID"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.put("/me", response_model=UserSessionResponse)
def update_current_session(
    update_data: UserSessionUpdate,
    current_session: UserSessionResponse = Depends(get_current_session),
    session_service: SessionService = Depends(get_session_service)
):
    """Update current session preferences and profile"""
    updated_session = session_service.update_session(
        current_session.session_id, 
        update_data
    )
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return updated_session


@router.put("/{session_id}", response_model=UserSessionResponse)
def update_session(
    session_id: str,
    update_data: UserSessionUpdate,
    session_service: SessionService = Depends(get_session_service)
):
    """Update session by ID"""
    updated_session = session_service.update_session(session_id, update_data)
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return updated_session


@router.put("/me/preferences", response_model=UserSessionResponse)
def update_preferences(
    preferences: UserPreferences,
    current_session: UserSessionResponse = Depends(get_current_session),
    session_service: SessionService = Depends(get_session_service)
):
    """Update user preferences for current session"""
    update_data = UserSessionUpdate(preferences=preferences)
    
    updated_session = session_service.update_session(
        current_session.session_id,
        update_data
    )
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return updated_session


@router.put("/me/health-profile", response_model=UserSessionResponse)
def update_health_profile(
    health_profile: HealthProfile,
    current_session: UserSessionResponse = Depends(get_current_session),
    session_service: SessionService = Depends(get_session_service)
):
    """Update health profile for current session"""
    update_data = UserSessionUpdate(health_profile=health_profile)
    
    updated_session = session_service.update_session(
        current_session.session_id,
        update_data
    )
    
    if not updated_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return updated_session


@router.delete("/me")
def delete_current_session(
    current_session: UserSessionResponse = Depends(get_current_session),
    session_service: SessionService = Depends(get_session_service)
):
    """Delete current session"""
    success = session_service.delete_session(current_session.session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": "Session deleted successfully"}


@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Delete session by ID"""
    success = session_service.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": "Session deleted successfully"}


@router.post("/me/trip-completed")
def record_trip_completion(
    current_session: UserSessionResponse = Depends(get_current_session),
    session_service: SessionService = Depends(get_session_service)
):
    """Record that a trip was completed for the current session"""
    success = session_service.increment_trip_count(current_session.session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": "Trip count updated"}


@router.post("/me/add-eco-score")
def add_eco_score(
    points: int,
    current_session: UserSessionResponse = Depends(get_current_session),
    session_service: SessionService = Depends(get_session_service)
):
    """Add eco score points to current session"""
    success = session_service.add_eco_score(current_session.session_id, points)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": f"Added {points} eco score points"}