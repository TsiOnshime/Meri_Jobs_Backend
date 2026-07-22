from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class ValidationMiddleware(MiddlewareMixin):
    """
    Request validation middleware.
    Validates request structure and content.
    """
    
    def process_request(self, request):
        # Skip validation for GET requests and health check
        if request.method in ['GET', 'HEAD', 'OPTIONS'] or request.path == '/health':
            return None
        
        # Validate Content-Type for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.content_type
            
            # For file uploads, allow multipart/form-data
            if request.path.startswith('/api/v1/cv/upload'):
                if not content_type or not content_type.startswith('multipart/form-data'):
                    return JsonResponse(
                        {
                            'error': {
                                'code': 'VALIDATION_ERROR',
                                'message': 'Content-Type must be multipart/form-data for file upload'
                            }
                        },
                        status=400
                    )
            # For other requests, require JSON
            elif not content_type or not content_type.startswith('application/json'):
                return JsonResponse(
                    {
                        'error': {
                            'code': 'VALIDATION_ERROR',
                            'message': 'Content-Type must be application/json'
                        }
                    },
                    status=400
                )
        
        return None
