from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for API Gateway.
    Ensures all errors follow the standard error format.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Convert to standard error format
        error_data = {
            'error': {
                'code': getattr(exc, 'default_code', 'ERROR'),
                'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc)
            }
        }
        
        # Add correlation ID if available
        request = context.get('request')
        if request and hasattr(request, 'correlation_id'):
            error_data['correlation_id'] = request.correlation_id
        
        response.data = error_data
        logger.error(f"Error: {error_data} for {request.path if request else 'unknown'}")
    
    else:
        # Handle non-API exceptions
        error_data = {
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        }
        
        request = context.get('request')
        if request and hasattr(request, 'correlation_id'):
            error_data['correlation_id'] = request.correlation_id
        
        logger.error(f"Unhandled exception: {exc} for {request.path if request else 'unknown'}")
        response = Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response
