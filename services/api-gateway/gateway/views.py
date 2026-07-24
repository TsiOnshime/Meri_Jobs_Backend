from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .clients.user_service import UserServiceClient
from .clients.matching_engine import MatchingEngineClient
from .auth.jwt import JWTAuthentication
import uuid


def error_response(code, message, status_code=status.HTTP_400_BAD_REQUEST):
    """Standard error response format matching frontend spec."""
    return Response({
        "error": {
            "code": code,
            "message": message
        },
        "correlation_id": str(uuid.uuid4())
    }, status=status_code)


@api_view(["GET"])
def health(request):
    """Liveness check -- used by docker-compose / orchestration."""
    return JsonResponse({"status": "ok", "service": "api-gateway"})


@api_view(["GET"])
def service_health(request):
    """Health check for all backend services."""
    user_client = UserServiceClient()
    matching_client = MatchingEngineClient()
    
    services = {
        "api-gateway": {"status": "ok"},
        "users": user_client.health_check(),
        "matching-engine": matching_client.health_check(),
    }
    
    return Response(services)


# Authentication endpoints
@api_view(["POST"])
def auth_register(request):
    """Proxy registration request to users service."""
    user_client = UserServiceClient()
    
    result = user_client.register_user(request.data)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def auth_login(request):
    """Proxy login request to users service."""
    user_client = UserServiceClient()
    email = request.data.get("email")
    password = request.data.get("password")
    
    if not email or not password:
        return error_response("VALIDATION_ERROR", "Email and password are required")
    
    result = user_client.login_user(email, password)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(["POST"])
def auth_refresh(request):
    """Proxy token refresh request to users service."""
    user_client = UserServiceClient()
    refresh_token = request.data.get("refresh")
    
    if not refresh_token:
        return error_response("VALIDATION_ERROR", "Refresh token is required")
    
    result = user_client.refresh_token(refresh_token)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(["POST"])
def auth_logout(request):
    """Proxy logout request to users service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    user_client = UserServiceClient()
    
    result = user_client.logout(request.data.get("refresh"), auth_header.replace("Bearer ", ""))
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(["GET"])
def auth_me(request):
    """Proxy current user request to users service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    user_client = UserServiceClient()
    
    result = user_client.get_me(auth_header.replace("Bearer ", ""))
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["POST"])
def auth_change_password(request):
    """Proxy password change request to users service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    user_client = UserServiceClient()
    
    result = user_client.change_password(request.data, auth_header.replace("Bearer ", ""))
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["GET", "PUT"])
def profile(request):
    """Proxy profile request to users service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    user_client = UserServiceClient()
    
    if request.method == "GET":
        result = user_client.get_profile(auth_header.replace("Bearer ", ""))
    else:  # PUT
        result = user_client.update_profile(request.data, auth_header.replace("Bearer ", ""))
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["GET", "PUT"])
def profile_detail(request):
    """Proxy profile detail request to users service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    user_client = UserServiceClient()
    
    if request.method == "GET":
        result = user_client.get_profile_detail(auth_header.replace("Bearer ", ""))
    else:  # PUT
        result = user_client.update_profile_detail(request.data, auth_header.replace("Bearer ", ""))
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


# CV Parser endpoints (proxied to cv-parser service)
@api_view(["POST"])
def cv_upload(request):
    """Proxy CV upload request to cv-parser service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Implement cv-parser client
    return error_response("SERVICE_UNAVAILABLE", "CV Parser service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["GET"])
def cv_status(request, cv_id):
    """Proxy CV status request to cv-parser service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Implement cv-parser client
    return error_response("SERVICE_UNAVAILABLE", "CV Parser service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["PATCH"])
def cv_update(request, cv_id):
    """Proxy CV update request to cv-parser service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Implement cv-parser client
    return error_response("SERVICE_UNAVAILABLE", "CV Parser service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["GET"])
def cv_export(request, cv_id):
    """Proxy CV export request to cv-parser service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Implement cv-parser client
    return error_response("SERVICE_UNAVAILABLE", "CV Parser service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["POST"])
def cv_suggestions_accept(request, cv_id):
    """Proxy CV suggestion accept request to cv-parser service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Implement cv-parser client
    return error_response("SERVICE_UNAVAILABLE", "CV Parser service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


# Matching Engine endpoints
@api_view(["GET"])
def matches_list(request, cv_id):
    """Proxy matches list request to matching engine."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    min_score = request.query_params.get("min_score")
    limit = int(request.query_params.get("limit", 20))
    offset = int(request.query_params.get("offset", 0))
    sort = request.query_params.get("sort", "score")
    
    matching_client = MatchingEngineClient()
    result = matching_client.get_matches_by_cv(cv_id, min_score, limit, offset, sort)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["GET"])
def match_detail(request, cv_id, job_id):
    """Proxy match detail request to matching engine."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    matching_client = MatchingEngineClient()
    result = matching_client.get_match_detail(cv_id, job_id)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


# Interview Prep endpoints (proxied to interview-prep service)
@api_view(["POST"])
def interview_session(request):
    """Proxy interview session creation to interview-prep service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Implement interview-prep client
    return error_response("SERVICE_UNAVAILABLE", "Interview Prep service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["POST"])
def interview_answer(request, session_id):
    """Proxy interview answer submission to interview-prep service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Implement interview-prep client
    return error_response("SERVICE_UNAVAILABLE", "Interview Prep service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["GET"])
def interview_answer_feedback(request, answer_id):
    """Proxy interview answer feedback request to interview-prep service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Implement interview-prep client
    return error_response("SERVICE_UNAVAILABLE", "Interview Prep service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["GET"])
def interview_history(request):
    """Proxy interview history request to interview-prep service."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    limit = int(request.query_params.get("limit", 10))
    offset = int(request.query_params.get("offset", 0))
    job_id = request.query_params.get("job_id")
    
    # TODO: Implement interview-prep client
    return error_response("SERVICE_UNAVAILABLE", "Interview Prep service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


# Dashboard endpoint
@api_view(["GET"])
def dashboard(request):
    """Aggregate dashboard data from multiple services."""
    jwt_auth = JWTAuthentication()
    user, token = jwt_auth.authenticate(request)
    
    if not user or not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return error_response("AUTH_INVALID_TOKEN", "Authentication required", status.HTTP_401_UNAUTHORIZED)
    
    # TODO: Aggregate data from users, cv-parser, matching-engine, and interview-prep
    return error_response("SERVICE_UNAVAILABLE", "Dashboard aggregation not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)
