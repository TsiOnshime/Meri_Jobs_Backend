import uuid
from django.utils.deprecation import MiddlewareMixin


class CorrelationMiddleware(MiddlewareMixin):
    """
    Adds a unique correlation ID to each request for tracing.
    """
    
    def process_request(self, request):
        # Check if correlation ID exists in headers
        correlation_id = request.META.get('HTTP_X_CORRELATION_ID')
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Attach to request
        request.correlation_id = correlation_id
        
        return None
    
    def process_response(self, request, response):
        # Add correlation ID to response headers
        if hasattr(request, 'correlation_id'):
            response['X-Correlation-ID'] = request.correlation_id
        
        return response
