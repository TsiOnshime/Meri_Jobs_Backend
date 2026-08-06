"""HTTP client for CV Parser service."""
from typing import Dict, Any, Optional
import requests
from decouple import config


class CVParserClient:
    """Client for CV Parser service."""
    
    def __init__(self):
        self.base_url = config(
            "CV_PARSER_URL", 
            default="http://cv-parser:8001"
        )
        self.timeout = 10
        self.auth_token = None
        self.internal_token = config("INTERNAL_SHARED_TOKEN", default="dev-internal-token")
    
    def set_auth_token(self, token: str):
        """Set authentication token for requests."""
        self.auth_token = token
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to CV parser service."""
        url = f"{self.base_url}{endpoint}"
        
        # Ensure headers dict exists
        if headers is None:
            headers = {}
        
        # Add internal token for service-to-service communication
        headers["X-Internal-Token"] = self.internal_token
        
        # Add auth token if available
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # For file uploads, don't set Content-Type - let requests set it with proper boundary
        if files:
            headers.pop("Content-Type", None)
            headers.pop("Accept", None)
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            elif method == "POST":
                # Don't use json=data when files are present
                if files:
                    response = requests.post(url, data=data, headers=headers, files=files, timeout=self.timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=self.timeout)
            elif method == "PATCH":
                response = requests.patch(url, json=data, headers=headers, timeout=self.timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle response
            if response.status_code >= 400:
                return {"error": response.text}
            
            return response.json()
            
        except requests.exceptions.Timeout:
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def upload_cv(self, file_obj, user_id: str) -> Dict[str, Any]:
        """Upload CV file for parsing."""
        file_obj.seek(0)
        file_bytes = file_obj.read()
        files = {"file": (file_obj.name, file_bytes)}
        data = {"user_id": user_id}
        
        return self._make_request("POST", "/internal/cv/upload", files=files, data=data)
    def get_cv_status(self, cv_id: str) -> Dict[str, Any]:
        """Get CV parsing status."""
        return self._make_request(
            "GET",
            f"/internal/cv/{cv_id}/status"
        )
    
    def get_cv(self, cv_id: str) -> Dict[str, Any]:
        """Get CV details."""
        return self._make_request(
            "GET",
            f"/internal/cv/{cv_id}"
        )
    
    def update_cv(self, cv_id: str, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update CV details."""
        return self._make_request(
            "PATCH",
            f"/internal/cv/{cv_id}",
            data=cv_data
        )
    
    def export_cv(self, cv_id: str, format: str = "pdf") -> Dict[str, Any]:
        """Export CV to specified format."""
        return self._make_request(
            "GET",
            f"/internal/cv/{cv_id}/export",
            params={"format": format}
        )
    
    def accept_suggestion(self, cv_id: str, suggestion_id: str) -> Dict[str, Any]:
        """Accept a CV suggestion."""
        return self._make_request(
            "POST",
            f"/internal/cv/{cv_id}/suggestions/accept",
            data={"suggestion_id": suggestion_id}
        )
    
    def accept_all_suggestions(self, cv_id: str) -> Dict[str, Any]:
        """Accept all CV suggestions."""
        return self._make_request(
            "POST",
            f"/internal/cv/{cv_id}/suggestions/accept-all"
        )
    
    def undo_suggestion(self, cv_id: str, suggestion_id: str) -> Dict[str, Any]:
        """Undo a CV suggestion."""
        return self._make_request(
            "POST",
            f"/internal/cv/{cv_id}/suggestions/undo",
            data={"suggestion_id": suggestion_id}
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Check CV parser service health."""
        return self._make_request("GET", "/internal/health")
