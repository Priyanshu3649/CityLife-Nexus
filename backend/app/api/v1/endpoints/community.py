"""
Community intelligence API endpoints for crowdsourced reporting
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_optional_session
from app.services.community_service import community_service
from app.schemas.base import CoordinatesSchema
from app.schemas.user import UserSessionResponse

router = APIRouter()


@router.post("/report")
async def submit_community_report(
    user_id: str,
    report_type: str,
    location: CoordinatesSchema,
    message: str,
    severity: str = Query("medium", regex="^(low|medium|high|critical)$")
):
    """
    Submit a new community report
    
    Args:
        user_id: ID of user submitting report
        report_type: Type of report (accident, signal_malfunction, road_hazard, construction, etc.)
        location: Location of incident
        message: Description of incident
        severity: Severity level
        
    Returns:
        Submitted report details
    """
    valid_report_types = [
        "accident", "signal_malfunction", "road_hazard", 
        "construction", "weather_impact", "other"
    ]
    
    if report_type not in valid_report_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Valid types: {valid_report_types}"
        )
    
    report = await community_service.submit_report(
        user_id=user_id,
        report_type=report_type,
        location=location,
        message=message,
        severity=severity
    )
    
    return report


@router.post("/reports-in-area")
async def get_reports_in_area(
    center: CoordinatesSchema,
    radius_km: float = Query(5.0, ge=0.1, le=50.0, description="Search radius in kilometers"),
    report_types: Optional[List[str]] = Query(None, description="Filter by report types"),
    min_trust_score: float = Query(0.3, ge=0.0, le=1.0, description="Minimum trust score threshold")
):
    """
    Get active reports in a specific area
    
    Args:
        center: Center coordinates
        radius_km: Search radius in kilometers
        report_types: Filter by report types (None for all)
        min_trust_score: Minimum trust score threshold
        
    Returns:
        List of reports in the area
    """
    reports = await community_service.get_reports_in_area(
        center=center,
        radius_km=radius_km,
        report_types=report_types,
        min_trust_score=min_trust_score
    )
    
    return {
        "center": center,
        "radius_km": radius_km,
        "reports_found": len(reports),
        "reports": reports
    }


@router.post("/vote")
async def vote_on_report(
    report_id: str,
    user_id: str,
    vote_type: str = Query(..., regex="^(upvote|downvote)$")
):
    """
    Vote on a community report
    
    Args:
        report_id: ID of report to vote on
        user_id: ID of user voting
        vote_type: Type of vote (upvote or downvote)
        
    Returns:
        Vote status
    """
    success = await community_service.vote_on_report(
        report_id=report_id,
        user_id=user_id,
        vote_type=vote_type
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Report {report_id} not found"
        )
    
    return {
        "report_id": report_id,
        "vote_type": vote_type,
        "voted": True,
        "message": "Vote recorded successfully"
    }


@router.post("/report-again")
async def report_incident_again(
    original_report_id: str,
    user_id: str
):
    """
    Report the same incident again (increases report count and refreshes timestamp)
    
    Args:
        original_report_id: ID of original report
        user_id: ID of user reporting
        
    Returns:
        Updated report data
    """
    updated_report = await community_service.report_incident_again(
        original_report_id=original_report_id,
        user_id=user_id
    )
    
    if not updated_report:
        raise HTTPException(
            status_code=404,
            detail=f"Original report {original_report_id} not found"
        )
    
    return updated_report


@router.get("/statistics")
async def get_community_report_statistics():
    """
    Get statistics about community reports
    
    Returns:
        Report statistics
    """
    stats = await community_service.get_report_statistics()
    return stats


@router.get("/user/{user_id}/contributions")
async def get_user_contributions(user_id: str):
    """
    Get statistics about a user's contributions
    
    Args:
        user_id: ID of user
        
    Returns:
        User contribution statistics
    """
    contributions = await community_service.get_user_contributions(user_id)
    return contributions


@router.post("/bulk-vote")
async def bulk_vote_on_reports(
    votes_data: List[dict]
):
    """
    Vote on multiple reports at once
    
    Args:
        votes_data: List of vote data dictionaries
        
    Returns:
        Voting results
    """
    if not votes_data:
        raise HTTPException(
            status_code=400,
            detail="At least one vote required"
        )
    
    if len(votes_data) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 votes allowed per request"
        )
    
    results = []
    
    for vote_data in votes_data:
        try:
            success = await community_service.vote_on_report(
                report_id=vote_data["report_id"],
                user_id=vote_data["user_id"],
                vote_type=vote_data["vote_type"]
            )
            
            results.append({
                "report_id": vote_data["report_id"],
                "user_id": vote_data["user_id"],
                "vote_type": vote_data["vote_type"],
                "success": success
            })
            
        except Exception as e:
            results.append({
                "report_id": vote_data.get("report_id", "unknown"),
                "user_id": vote_data.get("user_id", "unknown"),
                "vote_type": vote_data.get("vote_type", "unknown"),
                "success": False,
                "error": str(e)
            })
    
    successful_votes = sum(1 for r in results if r["success"])
    
    return {
        "total_votes": len(votes_data),
        "successful_votes": successful_votes,
        "results": results
    }