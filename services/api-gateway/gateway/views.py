from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


def health(request):
    """Liveness check -- used by docker-compose / orchestration."""
    return JsonResponse({"status": "ok", "service": "api-gateway"})


@csrf_exempt
@require_http_methods(["POST"])
def auth_register(request):
    """Proxy register request to users service"""
    from .clients.http_client import HttpClient
    from .events.producer import KafkaProducer
    import asyncio
    
    url = f"{settings.USERS_URL}/api/v1/auth/register"
    data = json.loads(request.body)
    
    client = HttpClient()
    result = asyncio.run(client.post(url, data=data))
    
    # Publish user registered event on success
    if result['status_code'] == 201:
        producer = KafkaProducer()
        user_data = result['data'].get('user', {})
        producer.publish_user_registered(
            user_data.get('id'),
            user_data.get('email'),
            user_data.get('name')
        )
    
    return JsonResponse(result['data'], status=result['status_code'])


@csrf_exempt
@require_http_methods(["POST"])
def auth_login(request):
    """Proxy login request to users service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.USERS_URL}/api/v1/auth/login"
    data = json.loads(request.body)
    
    client = HttpClient()
    result = asyncio.run(client.post(url, data=data))
    
    return JsonResponse(result['data'], status=result['status_code'])


@csrf_exempt
@require_http_methods(["POST"])
def auth_refresh(request):
    """Proxy token refresh request to users service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.USERS_URL}/api/v1/auth/refresh"
    data = json.loads(request.body)
    
    client = HttpClient()
    result = asyncio.run(client.post(url, data=data))
    
    return JsonResponse(result['data'], status=result['status_code'])


@csrf_exempt
@require_http_methods(["POST"])
def auth_logout(request):
    """Proxy logout request to users service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.USERS_URL}/api/v1/auth/logout"
    data = json.loads(request.body)
    
    client = HttpClient()
    result = asyncio.run(client.post(url, data=data))
    
    return JsonResponse(result['data'], status=result['status_code'])


@require_http_methods(["GET"])
def auth_me(request):
    """Proxy current user request to users service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.USERS_URL}/api/v1/auth/me"
    headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}
    
    client = HttpClient()
    result = asyncio.run(client.get(url, headers=headers))
    
    return JsonResponse(result['data'], status=result['status_code'])


# CV Parser Routing
@csrf_exempt
@require_http_methods(["POST"])
def cv_upload(request):
    """Proxy CV upload to cv-parser service"""
    from .clients.http_client import HttpClient
    from .events.producer import KafkaProducer
    import asyncio
    
    url = f"{settings.CV_PARSER_URL}/internal/cv/upload"
    data = {'user_id': request.user_id}
    files = {'file': request.FILES.get('file')}
    
    client = HttpClient()
    result = asyncio.run(client.post(url, data=data, files=files))
    
    # Publish CV uploaded event on success
    if result['status_code'] == 202:
        producer = KafkaProducer()
        cv_data = result['data']
        producer.publish_cv_uploaded(
            request.user_id,
            cv_data.get('cv_id'),
            request.FILES.get('file').name if request.FILES.get('file') else 'unknown'
        )
    
    return JsonResponse(result['data'], status=result['status_code'])


@require_http_methods(["GET"])
def cv_status(request, cv_id):
    """Proxy CV status request to cv-parser service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.CV_PARSER_URL}/internal/cv/{cv_id}/status"
    
    client = HttpClient()
    result = asyncio.run(client.get(url))
    
    return JsonResponse(result['data'], status=result['status_code'])


@csrf_exempt
@require_http_methods(["PATCH"])
def cv_edit(request, cv_id):
    """Proxy CV edit request to cv-parser service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.CV_PARSER_URL}/internal/cv/{cv_id}"
    data = json.loads(request.body)
    
    client = HttpClient()
    result = asyncio.run(client.patch(url, data=data))
    
    return JsonResponse(result['data'], status=result['status_code'])


@require_http_methods(["GET"])
def cv_export(request, cv_id):
    """Proxy CV export request to cv-parser service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.CV_PARSER_URL}/internal/cv/{cv_id}/export"
    
    client = HttpClient()
    result = asyncio.run(client.get(url))
    
    if result['status_code'] == 200:
        # Stream PDF response
        return HttpResponse(result['data'], content_type='application/pdf')
    
    return JsonResponse(result['data'], status=result['status_code'])


@csrf_exempt
@require_http_methods(["POST"])
def cv_suggestion_action(request, cv_id):
    """Proxy CV suggestion action to cv-parser service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.CV_PARSER_URL}/internal/cv/{cv_id}/suggestions/accept"
    data = json.loads(request.body)
    
    client = HttpClient()
    result = asyncio.run(client.post(url, data=data))
    
    return JsonResponse(result['data'], status=result['status_code'])


# Matching Engine Routing
@require_http_methods(["GET"])
def matches_list(request, cv_id):
    """Proxy matches list request to matching-engine service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.MATCHING_ENGINE_URL}/internal/matches/{cv_id}"
    params = {
        'min_score': request.GET.get('min_score'),
        'limit': request.GET.get('limit', 20),
        'offset': request.GET.get('offset', 0),
        'sort': request.GET.get('sort', 'score')
    }
    
    client = HttpClient()
    result = asyncio.run(client.get(url, params=params))
    
    return JsonResponse(result['data'], status=result['status_code'])


@require_http_methods(["GET"])
def match_detail(request, cv_id, job_id):
    """Proxy match detail request to matching-engine service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.MATCHING_ENGINE_URL}/internal/matches/{cv_id}/{job_id}"
    
    client = HttpClient()
    result = asyncio.run(client.get(url))
    
    return JsonResponse(result['data'], status=result['status_code'])


# Interview Prep Routing
@csrf_exempt
@require_http_methods(["POST"])
def interview_session(request):
    """Proxy interview session creation to interview-prep service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.INTERVIEW_PREP_URL}/internal/interview/session"
    data = json.loads(request.body)
    data['user_id'] = request.user_id
    
    client = HttpClient()
    result = asyncio.run(client.post(url, data=data))
    
    return JsonResponse(result['data'], status=result['status_code'])


@csrf_exempt
@require_http_methods(["POST"])
def interview_answer(request, session_id):
    """Proxy interview answer submission to interview-prep service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.INTERVIEW_PREP_URL}/internal/interview/{session_id}/answer"
    data = json.loads(request.body)
    
    client = HttpClient()
    result = asyncio.run(client.post(url, data=data))
    
    return JsonResponse(result['data'], status=result['status_code'])


@require_http_methods(["GET"])
def interview_answer_status(request, answer_id):
    """Proxy interview answer status check to interview-prep service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.INTERVIEW_PREP_URL}/internal/interview/answer/{answer_id}"
    
    client = HttpClient()
    result = asyncio.run(client.get(url))
    
    return JsonResponse(result['data'], status=result['status_code'])


@require_http_methods(["GET"])
def interview_history(request):
    """Proxy interview history request to interview-prep service"""
    from .clients.http_client import HttpClient
    import asyncio
    
    url = f"{settings.INTERVIEW_PREP_URL}/internal/interview/history/{request.user_id}"
    params = {
        'limit': request.GET.get('limit'),
        'offset': request.GET.get('offset'),
        'job_id': request.GET.get('job_id')
    }
    
    client = HttpClient()
    result = asyncio.run(client.get(url, params=params))
    
    return JsonResponse(result['data'], status=result['status_code'])


# Dashboard Aggregation
@require_http_methods(["GET"])
def dashboard(request):
    """Aggregate dashboard data from multiple services"""
    from .aggregation.dashboard_service import DashboardService
    import asyncio
    
    dashboard_service = DashboardService()
    dashboard_data = asyncio.run(dashboard_service.get_dashboard_data(request.user_id))
    
    return JsonResponse(dashboard_data, status=200)
