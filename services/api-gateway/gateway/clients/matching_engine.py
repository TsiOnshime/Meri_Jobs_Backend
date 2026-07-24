"""Thin HTTP client for calling matching-engines internal REST API."""
import requests
from decouple import config
from typing import Dict, Any, Optional


class MatchingEngineClient:
    """HTTP client for communicating with the Matching Engine service."""
    
    def __init__(self):
        self.base_url = config(
            "MATCHING_ENGINE_URL", 
            default="http://matching-engine:8002"
        )
        self.timeout = 10
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to matching engine service."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": f"Failed to communicate with matching engine: {str(e)}",
                "status": "error"
            }
    
    def get_matches_by_cv(
        self, 
        cv_id: str, 
        min_score: Optional[float] = None,
        limit: int = 20, 
        offset: int = 0, 
        sort: str = "score"
    ) -> Dict[str, Any]:
        """Get job matches for a CV."""
        params = {"limit": limit, "offset": offset, "sort": sort}
        if min_score is not None:
            params["min_score"] = min_score
        
        return self._make_request(
            "GET",
            f"/api/v1/matches/{cv_id}",
            params=params
        )
    
    def get_match_detail(self, cv_id: str, job_id: str) -> Dict[str, Any]:
        """Get detailed match analysis for a specific CV and job."""
        return self._make_request(
            "GET",
            f"/api/v1/matches/{cv_id}/{job_id}"
        )
    
    def create_match(self, user_id: str, job_id: str) -> Dict[str, Any]:
        """Create a new match between user and job."""
        return self._make_request(
            "POST",
            "/api/v1/matches",
            data={"user_id": user_id, "job_id": job_id}
        )
    
    def update_match_score(self, match_id: str, score: float) -> Dict[str, Any]:
        """Update match score."""
        return self._make_request(
            "PUT",
            f"/api/v1/matches/{match_id}",
            data={"score": score}
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Check matching engine service health."""
        return self._make_request("GET", "/health/")
