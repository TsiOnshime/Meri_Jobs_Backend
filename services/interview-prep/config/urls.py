from django.urls import path, include

urlpatterns = [
    path("internal/", include("prep.urls")),
]
