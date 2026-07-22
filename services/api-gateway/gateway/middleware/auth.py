from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(MiddlewareMixin):
    """
    JWT authentication middleware.
    Validates JWT tokens and attaches user info to request.
    """
    
    # Public paths that don't require authentication
    PUBLIC_PATHS = [
        '/health',
        '/api/v1/auth/register',
        '/api/v1/auth/login',
        '/api/v1/auth/refresh',
    ]
    
    def process_request(self, request):
        # Skip authentication for public paths
        if any(request.path.startswith(path) for path in self.PUBLIC_PATHS):
            return None
        
        # Get Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse(
                {
                    'error': {
                        'code': 'AUTH_MISSING_TOKEN',
                        'message': 'Missing authorization header'
                    }
                },
                status=401
            )
        
        token = auth_header.split(' ')[1]
        
        # Validate token (will be implemented with JWT validation)
        # For now, just attach a placeholder
        # TODO: Implement actual JWT validation
        try:
            # Placeholder - in production, validate with users service
            request.user_id = 'placeholder_user_id'
            request.user_role = 'user'
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return JsonResponse(
                {
                    'error': {
                        'code': 'AUTH_INVALID_TOKEN',
                        'message': 'Invalid or expired token'
                    }
                },
                status=401
            )
