"""Thin HTTP client for calling users service internal REST API."""
import requests
from decouple import config
from typing import Dict, Any, Optional


class UserServiceClient:
    """HTTP client for communicating with the User Service."""
    
    def __init__(self):
        self.base_url = config(
            "USERS_SERVICE_URL", 
            default="http://users:8001"
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
        """Make HTTP request to users service."""
        url = f"{self.base_url}{endpoint}"
        
        # Ensure headers dict exists
        if headers is None:
            headers = {}
        
        # Forward Authorization header if provided
        # This is for service-to-service authentication
        if "Authorization" not in headers and hasattr(self, 'auth_token') and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
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
                "error": f"Failed to communicate with users service: {str(e)}",
                "status": "error"
            }
    
    def set_auth_token(self, auth_token: str):
        """Set authentication token for service-to-service requests."""
        self.auth_token = auth_token
    
    def get_user(self, user_id: str, auth_token: str) -> Dict[str, Any]:
        """Get user details by ID."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "GET",
            f"/api/v1/profile/",
            headers=headers
        )
    
    def get_user_profile(self, user_id: str, auth_token: str) -> Dict[str, Any]:
        """Get user profile details."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "GET",
            "/api/v1/profile/detail/",
            headers=headers
        )
    
    def update_user_profile(
        self, 
        user_id: str, 
        profile_data: Dict[str, Any], 
        auth_token: str
    ) -> Dict[str, Any]:
        """Update user profile."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "PUT",
            "/api/v1/profile/detail/",
            data=profile_data,
            headers=headers
        )
    
    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user."""
        return self._make_request(
            "POST",
            "/api/v1/auth/register/",
            data=user_data
        )
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and get tokens."""
        return self._make_request(
            "POST",
            "/api/v1/auth/login/",
            data={"email": email, "password": password}
        )
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        return self._make_request(
            "POST",
            "/api/v1/auth/refresh/",
            data={"refresh": refresh_token}
        )
    
    def logout(self, refresh_token: str, auth_token: str) -> Dict[str, Any]:
        """Logout user by blacklisting refresh token."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "POST",
            "/api/v1/auth/logout/",
            data={"refresh": refresh_token},
            headers=headers
        )
    
    def get_me(self, auth_token: str) -> Dict[str, Any]:
        """Get current authenticated user."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "GET",
            "/api/v1/auth/me/",
            headers=headers
        )
    
    def change_password(self, password_data: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        """Change user password."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "POST",
            "/api/v1/auth/change-password/",
            data=password_data,
            headers=headers
        )
    
    def get_profile(self, auth_token: str) -> Dict[str, Any]:
        """Get user profile."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "GET",
            "/api/v1/profile/",
            headers=headers
        )
    
    def update_profile(self, profile_data: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        """Update user profile."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "PUT",
            "/api/v1/profile/",
            data=profile_data,
            headers=headers
        )
    
    def get_profile_detail(self, auth_token: str) -> Dict[str, Any]:
        """Get user profile details."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "GET",
            "/api/v1/profile/detail/",
            headers=headers
        )
    
    def update_profile_detail(self, profile_data: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        """Update user profile details."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        return self._make_request(
            "PUT",
            "/api/v1/profile/detail/",
            data=profile_data,
            headers=headers
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Check users service health."""
        return self._make_request("GET", "/api/v1/health/")
