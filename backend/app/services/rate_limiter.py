"""
Rate limiting service for external API calls
"""
import time
from typing import Dict, Optional
from collections import defaultdict, deque


class RateLimiter:
    """Simple in-memory rate limiter for API calls"""
    
    def __init__(self):
        # Store request timestamps for each service
        self.request_history: Dict[str, deque] = defaultdict(deque)
        # Rate limits per service (requests per minute)
        self.rate_limits = {
            "google_maps": 60,  # 60 requests per minute
            "openaq": 100,      # 100 requests per minute
            "default": 30       # Default limit
        }
    
    def is_allowed(self, service: str, identifier: Optional[str] = None) -> bool:
        """
        Check if a request is allowed based on rate limits
        
        Args:
            service: Service name (e.g., 'google_maps')
            identifier: Optional identifier for per-user limits
        
        Returns:
            True if request is allowed, False otherwise
        """
        key = f"{service}:{identifier}" if identifier else service
        limit = self.rate_limits.get(service, self.rate_limits["default"])
        
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Clean old requests outside the window
        history = self.request_history[key]
        while history and history[0] < window_start:
            history.popleft()
        
        # Check if we're under the limit
        if len(history) < limit:
            history.append(current_time)
            return True
        
        return False
    
    def get_reset_time(self, service: str, identifier: Optional[str] = None) -> float:
        """
        Get the time when the rate limit will reset
        
        Returns:
            Timestamp when the oldest request will expire
        """
        key = f"{service}:{identifier}" if identifier else service
        history = self.request_history[key]
        
        if not history:
            return time.time()
        
        return history[0] + 60  # Oldest request + 1 minute
    
    def get_remaining_requests(self, service: str, identifier: Optional[str] = None) -> int:
        """
        Get the number of remaining requests in the current window
        """
        key = f"{service}:{identifier}" if identifier else service
        limit = self.rate_limits.get(service, self.rate_limits["default"])
        
        current_time = time.time()
        window_start = current_time - 60
        
        # Clean old requests
        history = self.request_history[key]
        while history and history[0] < window_start:
            history.popleft()
        
        return max(0, limit - len(history))


# Global rate limiter instance
rate_limiter = RateLimiter()