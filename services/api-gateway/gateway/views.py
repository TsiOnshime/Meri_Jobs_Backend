from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .clients.user_service import UserServiceClient
from .clients.matching_engine import MatchingEngineClient
from .clients.cv_parser import CVParserClient
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
    # Authentication is handled by middleware
    user_client = UserServiceClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        user_client.set_auth_token(auth_token)
    
    result = user_client.logout(request.data.get("refresh"), auth_token)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(["GET"])
def auth_me(request):
    """Proxy current user request to users service."""
    # Authentication is handled by middleware
    user_client = UserServiceClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        user_client.set_auth_token(auth_token)
    
    result = user_client.get_me(auth_token)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["POST"])
def auth_change_password(request):
    """Proxy password change request to users service."""
    # Authentication is handled by middleware
    user_client = UserServiceClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        user_client.set_auth_token(auth_token)
    
    result = user_client.change_password(request.data, auth_token)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["GET", "PUT"])
def profile(request):
    """Proxy profile request to users service."""
    # Authentication is handled by middleware
    user_client = UserServiceClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        user_client.set_auth_token(auth_token)
    
    # Use detail parameter to determine which endpoint to call
    detail = request.query_params.get("detail", "false").lower() == "true"
    
    if request.method == "GET":
        if detail:
            result = user_client.get_profile_detail(auth_token)
        else:
            result = user_client.get_profile(auth_token)
    else:  # PUT
        if detail:
            result = user_client.update_profile_detail(request.data, auth_token)
        else:
            result = user_client.update_profile(request.data, auth_token)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


# CV Parser endpoints (proxied to cv-parser service)
@api_view(["POST"])
def cv_upload(request):
    """Proxy CV upload request to cv-parser service."""
    # Authentication is handled by middleware
    cv_client = CVParserClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        cv_client.set_auth_token(auth_token)
    
    # Use user_id from JWT token (already validated by middleware)
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return error_response("VALIDATION_ERROR", "User ID required from authentication")
    
    # Try to get file from FILES (if multipart parsing worked)
    file_obj = request.FILES.get("file")
    
    # If not in FILES, try to manually parse the request
    if not file_obj and hasattr(request, 'body'):
        # Manual multipart parsing for clients sending wrong Content-Type
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # This is a fallback - if the body contains file data, try to extract it
        # For now, return a helpful error
        return error_response("INVALID_REQUEST", "File upload failed. Ensure Content-Type is multipart/form-data", status.HTTP_400_BAD_REQUEST)
    
    if not file_obj:
        return error_response("VALIDATION_ERROR", "File required")
    
    # Pass Django file object directly - it's already file-like
    # Don't convert to BytesIO to preserve Django's file handling
    result = cv_client.upload_cv(file_obj, user_id)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def cv_status(request, cv_id):
    """Proxy CV status request to cv-parser service."""
    # Authentication is handled by middleware
    cv_client = CVParserClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        cv_client.set_auth_token(auth_token)
    
    result = cv_client.get_cv_status(cv_id)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["PATCH"])
def cv_update(request, cv_id):
    """Proxy CV update request to cv-parser service."""
    # Authentication is handled by middleware
    cv_client = CVParserClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        cv_client.set_auth_token(auth_token)
    
    result = cv_client.update_cv(cv_id, request.data)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["GET"])
def cv_export(request, cv_id):
    """Proxy CV export request to cv-parser service."""
    # Authentication is handled by middleware
    cv_client = CVParserClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        cv_client.set_auth_token(auth_token)
    
    format = request.query_params.get("format", "pdf")
    
    # For JSON format, return the parsed CV data from status endpoint
    # CV parser export only supports PDF
    if format == "json":
        status_result = cv_client.get_cv_status(cv_id)
        if "error" in status_result:
            return error_response("SERVICE_UNAVAILABLE", status_result.get("error"), status.HTTP_502_BAD_GATEWAY)
        return Response(status_result)
    
    # For PDF format, make direct request to CV parser
    url = f"{cv_client.base_url}/internal/cv/{cv_id}/export"
    headers = {"X-Internal-Token": cv_client.internal_token}
    
    try:
        import requests
        response = requests.get(url, params={"format": format}, headers=headers, timeout=cv_client.timeout)
        
        if response.status_code >= 400:
            # Try to parse error message from response
            error_msg = response.text
            return error_response("SERVICE_UNAVAILABLE", error_msg, status.HTTP_502_BAD_GATEWAY)
        
        # Return the binary PDF response
        from django.http import HttpResponse
        return HttpResponse(response.content, content_type="application/pdf")
            
    except requests.exceptions.Timeout:
        return error_response("SERVICE_UNAVAILABLE", "Request timeout", status.HTTP_502_BAD_GATEWAY)
    except requests.exceptions.RequestException as e:
        return error_response("SERVICE_UNAVAILABLE", str(e), status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
def cv_suggestions_accept(request, cv_id):
    """Proxy CV suggestion accept/reject/edit request to cv-parser service."""
    # Authentication is handled by middleware
    cv_client = CVParserClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        cv_client.set_auth_token(auth_token)
    
    suggestion_id = request.data.get("suggestion_id")
    action = request.data.get("action", "accept")  # Default to accept
    edited_text = request.data.get("edited_text")
    
    if not suggestion_id:
        return error_response("VALIDATION_ERROR", "Suggestion ID required")
    
    if action not in ("accept", "reject", "edit"):
        return error_response("VALIDATION_ERROR", "Action must be accept, reject, or edit")
    
    if action == "edit" and not edited_text:
        return error_response("VALIDATION_ERROR", "edited_text is required when action=edit")
    
    result = cv_client.accept_suggestion(cv_id, suggestion_id, action, edited_text)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["POST"])
def cv_suggestions_accept_all(request, cv_id):
    """Proxy CV suggestion accept-all request to cv-parser service."""
    # Authentication is handled by middleware
    cv_client = CVParserClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        cv_client.set_auth_token(auth_token)
    
    result = cv_client.accept_all_suggestions(cv_id)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["POST"])
def cv_suggestions_undo(request, cv_id):
    """Proxy CV suggestion undo request to cv-parser service."""
    # Authentication is handled by middleware
    cv_client = CVParserClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        cv_client.set_auth_token(auth_token)
    
    suggestion_id = request.data.get("suggestion_id")
    
    result = cv_client.undo_suggestion(cv_id, suggestion_id)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


# Matching Engine endpoints
@api_view(["GET"])
def matches_list(request, cv_id):
    """Proxy matches list request to matching engine."""
    # Authentication is handled by middleware
    min_score = request.query_params.get("min_score")
    limit = int(request.query_params.get("limit", 20))
    offset = int(request.query_params.get("offset", 0))
    sort = request.query_params.get("sort", "score")
    
    matching_client = MatchingEngineClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        matching_client.set_auth_token(auth_token)
    result = matching_client.get_matches_by_cv(cv_id, min_score, limit, offset, sort)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


@api_view(["GET"])
def match_detail(request, cv_id, job_id):
    """Proxy match detail request to matching engine."""
    # Authentication is handled by middleware
    matching_client = MatchingEngineClient()
    auth_token = getattr(request, 'auth_token', None)
    if auth_token:
        matching_client.set_auth_token(auth_token)
    result = matching_client.get_match_detail(cv_id, job_id)
    
    if "error" in result:
        return error_response("SERVICE_UNAVAILABLE", result.get("error"), status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)


# Interview Prep endpoints (proxied to interview-prep service)
@api_view(["POST"])
def interview_session(request):
    """Proxy interview session creation to interview-prep service."""
    # Authentication is handled by middleware
    # TODO: Implement interview-prep client
    return error_response("SERVICE_UNAVAILABLE", "Interview Prep service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["POST"])
def interview_answer(request, session_id):
    """Proxy interview answer submission to interview-prep service."""
    # Authentication is handled by middleware
    # TODO: Implement interview-prep client
    return error_response("SERVICE_UNAVAILABLE", "Interview Prep service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["GET"])
def interview_answer_feedback(request, answer_id):
    """Proxy interview answer feedback request to interview-prep service."""
    # Authentication is handled by middleware
    # TODO: Implement interview-prep client
    return error_response("SERVICE_UNAVAILABLE", "Interview Prep service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["GET"])
def interview_history(request):
    """Proxy interview history request to interview-prep service."""
    # Authentication is handled by middleware
    limit = int(request.query_params.get("limit", 10))
    offset = int(request.query_params.get("offset", 0))
    job_id = request.query_params.get("job_id")
    
    # TODO: Implement interview-prep client
    return error_response("SERVICE_UNAVAILABLE", "Interview Prep service not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)


# Dashboard endpoint
@api_view(["GET"])
def dashboard(request):
    """Aggregate dashboard data from multiple services."""
    # Authentication is handled by middleware
    # TODO: Aggregate data from users, cv-parser, matching-engine, and interview-prep
    return error_response("SERVICE_UNAVAILABLE", "Dashboard aggregation not yet implemented", status.HTTP_501_NOT_IMPLEMENTED)
