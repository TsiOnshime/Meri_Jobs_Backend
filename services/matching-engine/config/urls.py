from django.urls import path, include

urlpatterns = [
    path("internal/", include("matching.urls")),
]
