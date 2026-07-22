from rest_framework.exceptions import APIException


class GatewayException(APIException):
    """Base exception for API Gateway errors"""
    status_code = 500
    default_detail = "Internal gateway error"
    default_code = "GATEWAY_ERROR"


class ServiceUnavailableException(GatewayException):
    """Exception raised when a downstream service is unavailable"""
    status_code = 503
    default_detail = "Service temporarily unavailable"
    default_code = "SERVICE_UNAVAILABLE"


class RateLimitExceededException(GatewayException):
    """Exception raised when rate limit is exceeded"""
    status_code = 429
    default_detail = "Rate limit exceeded"
    default_code = "RATE_LIMIT_EXCEEDED"


class AuthenticationException(GatewayException):
    """Exception raised when authentication fails"""
    status_code = 401
    default_detail = "Authentication failed"
    default_code = "AUTH_ERROR"


class ValidationException(GatewayException):
    """Exception raised when request validation fails"""
    status_code = 400
    default_detail = "Request validation failed"
    default_code = "VALIDATION_ERROR"
