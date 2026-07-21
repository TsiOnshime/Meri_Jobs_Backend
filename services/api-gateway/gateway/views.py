from django.http import JsonResponse


def health(request):
    """Liveness check -- used by docker-compose / orchestration."""
    return JsonResponse({"status": "ok", "service": "api-gateway"})


# TODO: add this services real views here
