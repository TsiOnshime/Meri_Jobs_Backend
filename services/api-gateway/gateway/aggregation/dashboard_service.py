import asyncio
from django.conf import settings
from ..clients.http_client import HttpClient
import logging

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Aggregates data from multiple services for dashboard.
    """
    
    async def get_dashboard_data(self, user_id):
        """
        Fetch data from multiple services in parallel and combine.
        """
        # Define all service calls
        tasks = [
            self._get_user_info(user_id),
            self._get_cv_summary(user_id),
            self._get_match_summary(user_id),
            self._get_interview_summary(user_id)
        ]
        
        # Execute all calls in parallel (non-blocking)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any errors
        user_info = results[0] if not isinstance(results[0], Exception) else self._get_error_response()
        cv_summary = results[1] if not isinstance(results[1], Exception) else self._get_error_response()
        match_summary = results[2] if not isinstance(results[2], Exception) else self._get_error_response()
        interview_summary = results[3] if not isinstance(results[3], Exception) else self._get_error_response()
        
        # Combine into single response
        return {
            'user': user_info,
            'cv_summary': cv_summary,
            'match_summary': match_summary,
            'interview_summary': interview_summary
        }
    
    async def _get_user_info(self, user_id):
        """Call users service"""
        url = f"{settings.USERS_URL}/api/v1/auth/me"
        
        client = HttpClient()
        result = await client.get(url)
        
        if result['status_code'] == 200:
            return result['data'].get('user', {})
        return self._get_error_response()
    
    async def _get_cv_summary(self, user_id):
        """Call cv-parser service for CV summary"""
        # Note: cv-parser doesn't have a summary endpoint, so we'll return placeholder
        # In production, this would call a dedicated summary endpoint
        return {
            'total_cvs': 0,
            'latest_cv_id': None,
            'latest_cv_score': 0,
            'average_cv_score': 0
        }
    
    async def _get_match_summary(self, user_id):
        """Call matching-engine service for match summary"""
        # Note: matching-engine requires cv_id, not user_id
        # In production, we'd need to get user's CVs first
        return {
            'total_matches': 0,
            'high_priority_matches': 0,
            'average_match_score': 0
        }
    
    async def _get_interview_summary(self, user_id):
        """Call interview-prep service for interview summary"""
        url = f"{settings.INTERVIEW_PREP_URL}/internal/interview/history/{user_id}"
        
        client = HttpClient()
        result = await client.get(url)
        
        if result['status_code'] == 200:
            data = result['data']
            return {
                'practice_sessions': len(data.get('sessions', [])),
                'average_score': data.get('aggregated_stats', {}).get('average_score', 0),
                'strong_areas': data.get('aggregated_stats', {}).get('strong_areas', []),
                'weak_areas': data.get('aggregated_stats', {}).get('weak_areas', [])
            }
        return self._get_error_response()
    
    def _get_error_response(self):
        """Return default data when service is down"""
        return {
            'error': 'Service temporarily unavailable',
            'data': None
        }
