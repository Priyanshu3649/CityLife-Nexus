"""
Community intelligence service for crowdsourced hazard and signal reporting
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from app.schemas.base import CoordinatesSchema

logger = logging.getLogger(__name__)


class CommunityReport:
    """Represents a community-submitted report"""
    
    def __init__(
        self,
        report_id: str,
        user_id: str,
        report_type: str,  # "accident", "signal_malfunction", "road_hazard", "construction", etc.
        location: CoordinatesSchema,
        message: str,
        severity: str = "medium",  # "low", "medium", "high", "critical"
        expires_at: Optional[datetime] = None
    ):
        self.report_id = report_id
        self.user_id = user_id
        self.report_type = report_type
        self.location = location
        self.message = message
        self.severity = severity
        self.created_at = datetime.utcnow()
        self.expires_at = expires_at or (self.created_at + timedelta(hours=24))
        self.upvotes = 0
        self.downvotes = 0
        self.reports = 1  # Initial report count
        
    @property
    def trust_score(self) -> float:
        """Calculate trust score based on upvotes/downvotes and time decay"""
        # Simple trust score calculation
        net_votes = self.upvotes - self.downvotes
        total_votes = self.upvotes + self.downvotes
        
        # Base score from votes
        if total_votes == 0:
            vote_score = 0.5  # Neutral score if no votes
        else:
            vote_score = max(0.0, min(1.0, (net_votes + total_votes) / (2 * total_votes)))
        
        # Time decay factor (reports become less relevant over time)
        hours_since_creation = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        time_decay = max(0.1, 1.0 - (hours_since_creation / 24.0))  # Minimum 10% relevance
        
        # Report count factor (more reports = more trustworthy)
        report_factor = min(1.0, self.reports / 10.0)  # Cap at 10 reports
        
        return vote_score * time_decay * (0.7 + 0.3 * report_factor)  # Weighted combination
    
    @property
    def is_active(self) -> bool:
        """Check if report is still active (not expired)"""
        return datetime.utcnow() < self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "location": {
                "latitude": self.location.latitude,
                "longitude": self.location.longitude
            },
            "message": self.message,
            "severity": self.severity,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
            "reports": self.reports,
            "trust_score": round(self.trust_score, 3),
            "is_active": self.is_active
        }


class CommunityService:
    """Service for managing community reports and crowdsourced intelligence"""
    
    def __init__(self):
        self.reports = {}  # In-memory storage for demo
        self.user_report_counts = {}  # Track reports per user
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up expired reports"""
        # In a real implementation, this would be a proper background task
        # For demo, we'll just log that cleanup would happen
        logger.info("Community service cleanup task initialized")
    
    async def submit_report(
        self,
        user_id: str,
        report_type: str,
        location: CoordinatesSchema,
        message: str,
        severity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Submit a new community report
        
        Args:
            user_id: ID of user submitting report
            report_type: Type of report
            location: Location of incident
            message: Description of incident
            severity: Severity level
            
        Returns:
            Dictionary with report details
        """
        # Generate report ID
        import uuid
        report_id = str(uuid.uuid4())
        
        # Create report
        report = CommunityReport(
            report_id=report_id,
            user_id=user_id,
            report_type=report_type,
            location=location,
            message=message,
            severity=severity
        )
        
        # Store report
        self.reports[report_id] = report
        
        # Update user report count
        self.user_report_counts[user_id] = self.user_report_counts.get(user_id, 0) + 1
        
        logger.info(f"New community report submitted: {report_id} ({report_type})")
        
        return report.to_dict()
    
    async def get_reports_in_area(
        self,
        center: CoordinatesSchema,
        radius_km: float = 5.0,
        report_types: Optional[List[str]] = None,
        min_trust_score: float = 0.3
    ) -> List[Dict[str, Any]]:
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
        nearby_reports = []
        
        for report in self.reports.values():
            if not report.is_active:
                continue
                
            if report.trust_score < min_trust_score:
                continue
                
            if report_types and report.report_type not in report_types:
                continue
            
            distance = self._calculate_distance(center, report.location)
            if distance <= radius_km:
                report_dict = report.to_dict()
                report_dict["distance_km"] = round(distance, 2)
                nearby_reports.append(report_dict)
        
        # Sort by trust score (descending) and then by recency (descending)
        nearby_reports.sort(key=lambda x: (-x["trust_score"], x["created_at"]))
        
        return nearby_reports
    
    async def vote_on_report(
        self,
        report_id: str,
        user_id: str,
        vote_type: str  # "upvote" or "downvote"
    ) -> bool:
        """
        Vote on a community report
        
        Args:
            report_id: ID of report to vote on
            user_id: ID of user voting
            vote_type: Type of vote
            
        Returns:
            True if vote was successful, False otherwise
        """
        if report_id not in self.reports:
            return False
        
        report = self.reports[report_id]
        
        # In a real implementation, we'd track which users voted on which reports
        # For demo, we'll just update the vote counts
        
        if vote_type == "upvote":
            report.upvotes += 1
        elif vote_type == "downvote":
            report.downvotes += 1
        else:
            return False
        
        logger.info(f"Vote {vote_type} on report {report_id}")
        return True
    
    async def report_incident_again(
        self,
        original_report_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Report the same incident again (increases report count and refreshes timestamp)
        
        Args:
            original_report_id: ID of original report
            user_id: ID of user reporting
            
        Returns:
            Updated report data or None if not found
        """
        if original_report_id not in self.reports:
            return None
        
        report = self.reports[original_report_id]
        report.reports += 1
        report.expires_at = datetime.utcnow() + timedelta(hours=24)  # Refresh expiration
        
        # Update user report count
        self.user_report_counts[user_id] = self.user_report_counts.get(user_id, 0) + 1
        
        logger.info(f"Incident reported again: {original_report_id} (now {report.reports} reports)")
        
        return report.to_dict()
    
    async def get_report_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about community reports
        
        Returns:
            Dictionary with report statistics
        """
        active_reports = [r for r in self.reports.values() if r.is_active]
        
        if not active_reports:
            return {
                "total_reports": 0,
                "active_reports": 0,
                "report_types": {},
                "average_trust_score": 0.0,
                "total_upvotes": 0,
                "total_downvotes": 0
            }
        
        # Count report types
        type_counts = {}
        for report in active_reports:
            type_counts[report.report_type] = type_counts.get(report.report_type, 0) + 1
        
        # Calculate statistics
        total_upvotes = sum(r.upvotes for r in active_reports)
        total_downvotes = sum(r.downvotes for r in active_reports)
        avg_trust_score = sum(r.trust_score for r in active_reports) / len(active_reports)
        
        return {
            "total_reports": len(self.reports),
            "active_reports": len(active_reports),
            "report_types": type_counts,
            "average_trust_score": round(avg_trust_score, 3),
            "total_upvotes": total_upvotes,
            "total_downvotes": total_downvotes
        }
    
    async def get_user_contributions(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about a user's contributions
        
        Args:
            user_id: ID of user
            
        Returns:
            Dictionary with user contribution statistics
        """
        user_reports = [
            r for r in self.reports.values() 
            if r.user_id == user_id
        ]
        
        if not user_reports:
            return {
                "user_id": user_id,
                "total_reports": 0,
                "active_reports": 0,
                "report_types": {},
                "total_upvotes_received": 0,
                "total_downvotes_received": 0,
                "reputation_score": 0
            }
        
        # Count report types
        type_counts = {}
        for report in user_reports:
            type_counts[report.report_type] = type_counts.get(report.report_type, 0) + 1
        
        # Calculate statistics
        active_reports = [r for r in user_reports if r.is_active]
        upvotes_received = sum(r.upvotes for r in user_reports)
        downvotes_received = sum(r.downvotes for r in user_reports)
        
        # Simple reputation score
        reputation_score = upvotes_received - downvotes_received
        if len(user_reports) > 0:
            reputation_score += len(active_reports)  # Bonus for active reports
        
        return {
            "user_id": user_id,
            "total_reports": len(user_reports),
            "active_reports": len(active_reports),
            "report_types": type_counts,
            "total_upvotes_received": upvotes_received,
            "total_downvotes_received": downvotes_received,
            "reputation_score": reputation_score
        }
    
    async def cleanup_expired_reports(self):
        """Remove expired reports from memory"""
        expired_count = 0
        current_time = datetime.utcnow()
        
        expired_ids = [
            report_id for report_id, report in self.reports.items()
            if report.expires_at < current_time
        ]
        
        for report_id in expired_ids:
            del self.reports[report_id]
            expired_count += 1
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired community reports")
    
    def _calculate_distance(
        self,
        coord1: CoordinatesSchema,
        coord2: CoordinatesSchema
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Returns:
            Distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [
            coord1.latitude, coord1.longitude,
            coord2.latitude, coord2.longitude
        ])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r


# Global instance
community_service = CommunityService()