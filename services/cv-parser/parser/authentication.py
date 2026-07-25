from django.conf import settings
from rest_framework import authentication, exceptions


class InternalServiceUser:
    """No end-user identity here -- api-gateway already checked the real JWT."""
    is_authenticated = True

    def __str__(self):
        return "internal-service"


class InternalTokenAuthentication(authentication.BaseAuthentication):
    """Checks X-Internal-Token against a shared secret. Not user auth --
    just proves this request came from inside our own system."""

    def authenticate(self, request):
        token = request.headers.get("X-Internal-Token")
        if not token:
            return None
        if token != settings.INTERNAL_SHARED_TOKEN:
            raise exceptions.AuthenticationFailed("Invalid internal token")
        return (InternalServiceUser(), None)