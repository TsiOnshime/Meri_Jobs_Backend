from django.urls import path, include

urlpatterns = [
    path("internal/", include("ingestion.urls")),
]
