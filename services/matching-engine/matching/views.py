from django.http import JsonResponse
from django.core.paginator import Paginator
from matching.models import CV, Match

def health(request):
    """Liveness check -- used by docker-compose / orchestration."""
    return JsonResponse({"status": "ok", "service": "matching-engine"})


def list_matches(request, cv_id):
    #  GET /internal/matches/{cv_id}
    if not CV.objects.filter(cv_id=cv_id).exists():
        return JsonResponse(
            {"error": {"code": "cv_not_found","message": f"No CV record found for {cv_id}"}},status=404)
        
    min_score = float(request.GET.get("min_score", 0))
    limit = int(request.GET.get("limit", 20))
    offset = int(request.GET.get("offset", 0))
    sort = request.GET.get("sort", "score")
    
    queryset = Match.objects.filter(cv_id=cv_id, overall_score__gte=min_score).select_related("job")
    
    if sort == "recent":
        queryset = queryset.order_by("-computed_at")
    else:
        queryset = queryset.order_by("-overall_score")
        
    count = queryset.count()
    page = queryset[offset:offset + limit]
    
    results = [
        {
            "job_id": str(match.job_id), 
            "overall_score": match.overall_score,
            "source_url": match.job.source_url, 
            "computed_at": match.computed_at.isoformat(),
        }
        for match in page
    ]
    
    return JsonResponse({"cv_id": cv_id, "count": count, "results": results})

def match_detail(request, cv_id, job_id):
    #  GET /internal/matches/{cv_id}/{job_id} 
    
    match = Match.objects.filter(cv_id=cv_id, job_id=job_id).select_related("job").first()
    
    if match is None:
        return JsonResponse(
            {"error": {"code": "match_not_found", "message": f"No match found for {cv_id}"}},
            status=404
        )

    return JsonResponse({
        "cv_id": str(match.cv_id),
        "job_id": str(match.job_id),
        "overall_score": match.overall_score,
        "source_url": match.job.source_url, 
        "breakdown": match.breakdown,
        "computed_at": match.computed_at.isoformat()
    })
