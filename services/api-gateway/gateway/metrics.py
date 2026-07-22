from prometheus_client import Counter, Histogram, Gauge, generate_latest
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

# Metrics
request_count = Counter(
    'api_gateway_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_gateway_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'api_gateway_active_connections',
    'Number of active connections'
)

service_errors = Counter(
    'api_gateway_service_errors_total',
    'Total number of service errors',
    ['service', 'error_type']
)

rate_limit_blocks = Counter(
    'api_gateway_rate_limit_blocks_total',
    'Total number of rate limit blocks',
    ['endpoint']
)


def metrics_view(request):
    """Prometheus metrics endpoint"""
    return HttpResponse(
        generate_latest(),
        content_type='text/plain; version=0.0.4; charset=utf-8'
    )


def track_request(method, endpoint, status, duration):
    """Track request metrics"""
    request_count.labels(method=method, endpoint=endpoint, status=status).inc()
    request_duration.labels(method=method, endpoint=endpoint).observe(duration)


def track_service_error(service, error_type):
    """Track service error metrics"""
    service_errors.labels(service=service, error_type=error_type).inc()


def track_rate_limit_block(endpoint):
    """Track rate limit block metrics"""
    rate_limit_blocks.labels(endpoint=endpoint).inc()
