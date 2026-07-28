from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("matches/<uuid:cv_id>", views.list_matches, name="list-matches"),
    path("matches/<uuid:cv_id>/<uuid:job_id>", views.match_detail, name="match-detail"),
]
