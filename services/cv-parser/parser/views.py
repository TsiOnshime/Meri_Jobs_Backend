from django.http import JsonResponse


def health(request):
    """Liveness check -- used by docker-compose / orchestration."""
    return JsonResponse({"status": "ok", "service": "cv-parser"})


# TODO: add this services real views here
