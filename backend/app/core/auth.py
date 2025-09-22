"""
Authentication middleware and utilities
"""
from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.session_service import SessionService
from app.schemas.user import UserSessionResponse


security = HTTPBearer(auto_error=False)


class SessionAuth:
    """Session-based authentication for CityLife Nexus"""
    
    def __init__(self):
        pass
    
    def get_session_from_header(
        self, 
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> Optional[UserSessionResponse]:
        """
        Extract session ID from Authorization header or X-Session-ID header
        """
        session_id = None
        
        # Try to get session ID from Authorization header (Bearer token)
        if credentials:
            session_id = credentials.credentials
        
        # Try to get session ID from X-Session-ID header
        if not session_id:
            session_id = request.headers.get("X-Session-ID")
        
        if not session_id:
            return None
        
        # Validate session exists in database
        session_service = SessionService(db)
        user_session = session_service.get_session(session_id)
        
        return user_session
    
    def require_session(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> UserSessionResponse:
        """
        Require a valid session for the request
        """
        session_id = None
        
        # Try to get session ID from Authorization header (Bearer token)
        if credentials:
            session_id = credentials.credentials
        
        # Try to get session ID from X-Session-ID header
        if not session_id:
            session_id = request.headers.get("X-Session-ID")
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session ID required"
            )
        
        # Validate session exists in database
        session_service = SessionService(db)
        user_session = session_service.get_session(session_id)
        
        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        return user_session