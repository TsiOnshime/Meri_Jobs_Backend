import redis
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Redis-backed rate limiting middleware using fixed window counter.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=1,  # Separate DB for rate limiting
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
    
    def process_request(self, request):
        # Skip rate limiting for health check
        if request.path == '/health':
            return None
        
        # Get identifier (user_id if authenticated, IP otherwise)
        identifier = self._get_identifier(request)
        
        # Get endpoint type
        endpoint = self._get_endpoint_type(request.path)
        
        # Get rate limit config
        config = self._get_rate_limit_config(endpoint)
        
        # Check rate limit
        allowed = self._check_rate_limit(identifier, config)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {identifier} on {endpoint}")
            return JsonResponse(
                {
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': f"Rate limit exceeded: {config['requests_per_minute']} requests per minute"
                    }
                },
                status=429
            )
        
        return None
    
    def process_response(self, request, response):
        # Add rate limit headers
        if request.path != '/health':
            identifier = self._get_identifier(request)
            endpoint = self._get_endpoint_type(request.path)
            config = self._get_rate_limit_config(endpoint)
            remaining = self._get_remaining_requests(identifier, config)
            
            response['X-RateLimit-Limit-Minute'] = str(config['requests_per_minute'])
            response['X-RateLimit-Remaining-Minute'] = str(remaining['minute_remaining'])
        
        return response
    
    def _get_identifier(self, request):
        """Get unique identifier for rate limiting"""
        if hasattr(request, 'user_id'):
            return f"user:{request.user_id}"
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"ip:{ip}"
    
    def _get_endpoint_type(self, path):
        """Determine endpoint type from path"""
        if path.startswith('/api/v1/auth'):
            return 'auth'
        elif path.startswith('/api/v1/cv/upload'):
            return 'cv_upload'
        elif path.startswith('/api/v1/jobs'):
            return 'jobs'
        elif path.startswith('/api/v1/interview'):
            return 'interview'
        return 'default'
    
    def _get_rate_limit_config(self, endpoint):
        """Get rate limit configuration for endpoint"""
        configs = {
            'auth': {'requests_per_minute': 5, 'requests_per_hour': 20},
            'cv_upload': {'requests_per_minute': 2, 'requests_per_hour': 10},
            'jobs': {'requests_per_minute': 200, 'requests_per_hour': 2000},
            'interview': {'requests_per_minute': 10, 'requests_per_hour': 100},
            'default': {'requests_per_minute': 100, 'requests_per_hour': 1000}
        }
        return configs.get(endpoint, configs['default'])
    
    def _check_rate_limit(self, identifier, config):
        """Check if request is within rate limit"""
        try:
            key = f"ratelimit:{identifier}:minute"
            pipe = self.redis_client.pipeline()
            current = pipe.get(key)
            pipe.execute()
            
            if current is None:
                pipe.setex(key, 60, 1)
                pipe.execute()
                return True
            
            current = int(current)
            if current >= config['requests_per_minute']:
                pipe.reset()
                return False
            
            pipe.incr(key)
            pipe.expire(key, 60)
            pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Redis error in rate limiter: {e}")
            return True  # Fail open
    
    def _get_remaining_requests(self, identifier, config):
        """Get remaining requests for headers"""
        try:
            key = f"ratelimit:{identifier}:minute"
            current = int(self.redis_client.get(key) or 0)
            return {
                'minute_remaining': max(0, config['requests_per_minute'] - current)
            }
        except:
            return {'minute_remaining': config['requests_per_minute']}
