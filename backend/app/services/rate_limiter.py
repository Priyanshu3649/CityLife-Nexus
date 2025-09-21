"""
Simple rate limiter for API calls
"""
import time
from typing import Dict
from collections import defaultdict


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "google_maps": {"requests": 100, "window": 60},  # 100 requests per minute
            "openaq": {"requests": 50, "window": 60},        # 50 requests per minute
            "default": {"requests": 60, "window": 60}        # 60 requests per minute
        }
    
    def is_allowed(self, service: str) -> bool:
        """Check if a request is allowed for the given service"""
        current_time = time.time()
        limit_config = self.limits.get(service, self.limits["default"])
        
        # Clean old requests outside the time window
        cutoff_time = current_time - limit_config["window"]
        self.requests[service] = [
            req_time for req_time in self.requests[service] 
            if req_time > cutoff_time
        ]
        
        # Check if we're under the limit
        if len(self.requests[service]) < limit_config["requests"]:
            self.requests[service].append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, service: str) -> int:
        """Get the number of remaining requests for a service"""
        current_time = time.time()
        limit_config = self.limits.get(service, self.limits["default"])
        
        # Clean old requests
        cutoff_time = current_time - limit_config["window"]
        self.requests[service] = [
            req_time for req_time in self.requests[service] 
            if req_time > cutoff_time
        ]
        
        return max(0, limit_config["requests"] - len(self.requests[service]))
    
    def reset_service(self, service: str):
        """Reset the rate limit for a specific service"""
        self.requests[service] = []


# Global instance
rate_limiter = RateLimiter()