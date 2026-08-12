"""JWT authentication middleware for API Gateway."""
from django.http import JsonResponse
from ..auth.jwt import JWTAuthentication


class JWTAuthenticationMiddleware:
    """Middleware to validate JWT tokens for protected endpoints."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
    
    def __call__(self, request):
        # Skip authentication for public endpoints
        if self.jwt_auth.is_public_endpoint(request.path):
            return self.get_response(request)
        
        # Validate JWT token
        user_info, token = self.jwt_auth.authenticate(request)
        
        if not user_info:
            return self.jwt_auth.create_auth_error_response()
        
        # Add user info to request for downstream use
        request.user_id = user_info["id"]
        request.user_email = user_info["email"]
        request.user_info = user_info
        request.auth_token = token
        
        return self.get_response(request)
