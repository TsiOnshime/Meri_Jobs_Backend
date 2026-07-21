from django.urls import path, include

urlpatterns = [
    path("internal/", include("gateway.urls")),
]
