"""Per-user rate limiting middleware."""
import redis
from django.conf import settings
from django.http import JsonResponse
from decouple import config
from rest_framework.exceptions import Throttled
import uuid


class RateLimitMiddleware:
    """Redis-based rate limiting middleware for API Gateway with per-endpoint limits."""
    
    # Per-endpoint rate limits (requests per minute)
    ENDPOINT_LIMITS = {
        # Auth endpoints: 5 / minute
        "auth/register": 5,
        "auth/login": 5,
        "auth/refresh": 5,
        "auth/logout": 5,
        "auth/me": 5,
        
        # CV upload: 2 / minute
        "cv/upload": 2,
        
        # CV other endpoints: 20 / minute
        "cv/": 20,
        
        # Jobs/matching endpoints: 200 / minute
        "matches/": 200,
        
        # Interview endpoints: 10 / minute
        "interview/": 10,
        
        # Dashboard: 30 / minute
        "dashboard": 30,
        
        # Default: 100 / minute
        "default": 100
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.redis_client = redis.Redis(
            host=config("REDIS_HOST", default="redis"),
            port=config("REDIS_PORT", default=6379, cast=int),
            db=0,
            decode_responses=True
        )
        # Default hourly limit
        self.requests_per_hour = config("RATE_LIMIT_RPH", default=1000, cast=int)
    
    def __call__(self, request):
        # Skip rate limiting for health checks
        if request.path in ["/internal/health", "/api/v1/health", "/health"]:
            return self.get_response(request)
        
        # Get endpoint-specific limit
        endpoint_limit = self._get_endpoint_limit(request.path)
        
        # Get identifier (user ID if authenticated, otherwise IP)
        identifier = self._get_identifier(request)
        
        # Check rate limits
        if not self._check_rate_limit(identifier, endpoint_limit, request.path):
            return JsonResponse(
                {
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Please try again later."
                    },
                    "correlation_id": str(uuid.uuid4())
                },
                status=429
            )
        
        response = self.get_response(request)
        
        # Add rate limit headers
        response["X-RateLimit-Limit-Minute"] = str(endpoint_limit)
        response["X-RateLimit-Remaining-Minute"] = str(self._get_remaining_requests(identifier, request.path))
        
        return response
    
    def _get_endpoint_limit(self, path):
        """Get rate limit for specific endpoint."""
        # Remove /api/v1/ prefix if present
        clean_path = path.replace("/api/v1/", "").replace("/internal/", "")
        
        # Check for exact matches
        if clean_path in self.ENDPOINT_LIMITS:
            return self.ENDPOINT_LIMITS[clean_path]
        
        # Check for prefix matches
        for endpoint, limit in self.ENDPOINT_LIMITS.items():
            if endpoint != "default" and clean_path.startswith(endpoint):
                return limit
        
        # Return default limit
        return self.ENDPOINT_LIMITS["default"]
    
    def _get_identifier(self, request):
        """Get unique identifier for rate limiting (user ID or IP)."""
        # Try to get user ID from JWT authentication
        try:
            from ..auth.jwt import JWTAuthentication
            jwt_auth = JWTAuthentication()
            user_id = jwt_auth.get_user_id(request)
            if user_id:
                return f"user:{user_id}"
        except:
            pass
        
        # Fall back to IP address
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        
        return f"ip:{ip}"
    
    def _check_rate_limit(self, identifier, limit_per_minute, path):
        """Check if the identifier has exceeded rate limits."""
        clean_path = path.replace("/api/v1/", "").replace("/internal/", "")
        minute_key = f"ratelimit:{identifier}:{clean_path}:minute"
        hour_key = f"ratelimit:{identifier}:hour"
        
        try:
            # Check minute limit
            minute_count = self.redis_client.incr(minute_key)
            if minute_count == 1:
                self.redis_client.expire(minute_key, 60)
            
            if minute_count > limit_per_minute:
                return False
            
            # Check hour limit
            hour_count = self.redis_client.incr(hour_key)
            if hour_count == 1:
                self.redis_client.expire(hour_key, 3600)
            
            if hour_count > self.requests_per_hour:
                return False
            
            return True
            
        except redis.RedisError:
            # If Redis is unavailable, allow the request (fail open)
            return True
    
    def _get_remaining_requests(self, identifier, path):
        """Get remaining requests for the current minute."""
        clean_path = path.replace("/api/v1/", "").replace("/internal/", "")
        minute_key = f"ratelimit:{identifier}:{clean_path}:minute"
        endpoint_limit = self._get_endpoint_limit(path)
        
        try:
            current_count = int(self.redis_client.get(minute_key) or 0)
            return max(0, endpoint_limit - current_count)
        except redis.RedisError:
            return endpoint_limit
