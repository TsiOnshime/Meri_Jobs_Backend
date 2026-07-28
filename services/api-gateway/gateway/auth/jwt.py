"""JWT issuing and validation for logged-in users."""
import jwt
from decouple import config
from django.http import JsonResponse
from rest_framework import status
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class JWTAuthentication:
    """JWT token validation and user extraction for API Gateway."""
    
    def __init__(self):
        self.secret_key = config("JWT_SECRET_KEY", default="your-secret-key-change-in-production")
        self.algorithm = config("JWT_ALGORITHM", default="HS256")
        self.token_prefix = "Bearer "
    
    def authenticate(self, request) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate JWT token from Authorization header.
        
        Returns:
            Tuple of (user_info, token) or (None, None) if invalid
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        
        if not auth_header:
            logger.debug("No Authorization header found")
            return None, None
        
        if not auth_header.startswith(self.token_prefix):
            logger.debug(f"Invalid Authorization header format: {auth_header[:20]}...")
            return None, None
        
        token = auth_header[len(self.token_prefix):]
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            user_id = payload.get("user_id")
            email = payload.get("email")
            
            if not user_id:
                logger.warning("JWT token missing user_id in payload")
                return None, None
            
            user_info = {
                "id": user_id,
                "email": email,
                "is_authenticated": True
            }
            
            logger.debug(f"Successfully authenticated user: {user_id}")
            return user_info, token
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error during JWT validation: {str(e)}")
            return None, None
    
    def get_user_id(self, request) -> Optional[str]:
        """Extract user_id from request JWT token."""
        user_info, _ = self.authenticate(request)
        return user_info["id"] if user_info else None
    
    def get_user_info(self, request) -> Optional[Dict[str, Any]]:
        """Get complete user info from request JWT token."""
        user_info, _ = self.authenticate(request)
        return user_info
    
    def create_auth_error_response(self, error_code: str = "AUTH_INVALID_TOKEN", 
                                   message: str = "Authentication required") -> JsonResponse:
        """Create standardized authentication error response."""
        import uuid
        return JsonResponse(
            {
                "error": {
                    "code": error_code,
                    "message": message
                },
                "correlation_id": str(uuid.uuid4())
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint should skip authentication."""
        public_endpoints = [
            "/health",
            "/services/health",
            "/api/v1/health",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/schema"
        ]
        
        return any(path.startswith(endpoint) for endpoint in public_endpoints)
