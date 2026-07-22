import httpx
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class HttpClient:
    """
    HTTP client for making requests to internal services.
    Includes circuit breaker pattern and internal token authentication.
    """
    
    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
        self.circuit_breaker_threshold = settings.CIRCUIT_BREAKER_THRESHOLD
        self.circuit_breaker_timeout = settings.CIRCUIT_BREAKER_TIMEOUT
        self.failure_counts = {}
        self.last_failure_time = {}
    
    async def post(self, url, data=None, headers=None, files=None):
        """Make POST request to internal service"""
        return await self._request('POST', url, data=data, headers=headers, files=files)
    
    async def get(self, url, params=None, headers=None):
        """Make GET request to internal service"""
        return await self._request('GET', url, params=params, headers=headers)
    
    async def patch(self, url, data=None, headers=None):
        """Make PATCH request to internal service"""
        return await self._request('PATCH', url, data=data, headers=headers)
    
    async def delete(self, url, headers=None):
        """Make DELETE request to internal service"""
        return await self._request('DELETE', url, headers=headers)
    
    async def _request(self, method, url, data=None, params=None, headers=None, files=None):
        """Make HTTP request with circuit breaker and internal token"""
        # Check circuit breaker
        if self._is_circuit_open(url):
            logger.warning(f"Circuit breaker open for {url}")
            return {
                'status_code': 503,
                'data': {
                    'error': {
                        'code': 'SERVICE_UNAVAILABLE',
                        'message': 'Service temporarily unavailable'
                    }
                }
            }
        
        # Add internal token to headers
        if headers is None:
            headers = {}
        headers['X-Internal-Token'] = settings.INTERNAL_TOKEN
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == 'POST':
                    response = await client.post(url, json=data, headers=headers, files=files)
                elif method == 'GET':
                    response = await client.get(url, params=params, headers=headers)
                elif method == 'PATCH':
                    response = await client.patch(url, json=data, headers=headers)
                elif method == 'DELETE':
                    response = await client.delete(url, headers=headers)
                
                # Reset failure count on success
                self._reset_failure_count(url)
                
                return {
                    'status_code': response.status_code,
                    'data': response.json() if response.content else None
                }
                
        except httpx.TimeoutException:
            self._record_failure(url)
            logger.error(f"Timeout error for {url}")
            return {
                'status_code': 504,
                'data': {
                    'error': {
                        'code': 'GATEWAY_TIMEOUT',
                        'message': 'Service timeout'
                    }
                }
            }
        except Exception as e:
            self._record_failure(url)
            logger.error(f"Request error for {url}: {e}")
            return {
                'status_code': 502,
                'data': {
                    'error': {
                        'code': 'BAD_GATEWAY',
                        'message': 'Service error'
                    }
                }
            }
    
    def _is_circuit_open(self, url):
        """Check if circuit breaker is open for this service"""
        failure_count = self.failure_counts.get(url, 0)
        last_failure = self.last_failure_time.get(url, 0)
        
        if failure_count >= self.circuit_breaker_threshold:
            # Check if timeout has passed
            import time
            if time.time() - last_failure < self.circuit_breaker_timeout:
                return True
            else:
                # Timeout passed, reset
                self._reset_failure_count(url)
        
        return False
    
    def _record_failure(self, url):
        """Record a failure for circuit breaker"""
        import time
        self.failure_counts[url] = self.failure_counts.get(url, 0) + 1
        self.last_failure_time[url] = time.time()
    
    def _reset_failure_count(self, url):
        """Reset failure count after successful request"""
        self.failure_counts[url] = 0
