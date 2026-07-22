from django.urls import path
from . import views
from . import metrics

urlpatterns = [
    path("health", views.health, name="health"),
    path("metrics", metrics.metrics_view, name="metrics"),
    # Auth endpoints
    path("api/v1/auth/register", views.auth_register, name="auth_register"),
    path("api/v1/auth/login", views.auth_login, name="auth_login"),
    path("api/v1/auth/refresh", views.auth_refresh, name="auth_refresh"),
    path("api/v1/auth/logout", views.auth_logout, name="auth_logout"),
    path("api/v1/auth/me", views.auth_me, name="auth_me"),
    # CV endpoints
    path("api/v1/cv/upload", views.cv_upload, name="cv_upload"),
    path("api/v1/cv/<uuid:cv_id>/status", views.cv_status, name="cv_status"),
    path("api/v1/cv/<uuid:cv_id>", views.cv_edit, name="cv_edit"),
    path("api/v1/cv/<uuid:cv_id>/export", views.cv_export, name="cv_export"),
    path("api/v1/cv/<uuid:cv_id>/suggestions/accept", views.cv_suggestion_action, name="cv_suggestion_action"),
    # Match endpoints
    path("api/v1/matches/<uuid:cv_id>", views.matches_list, name="matches_list"),
    path("api/v1/matches/<uuid:cv_id>/<uuid:job_id>", views.match_detail, name="match_detail"),
    # Interview endpoints
    path("api/v1/interview/session", views.interview_session, name="interview_session"),
    path("api/v1/interview/session/<uuid:session_id>/answer", views.interview_answer, name="interview_answer"),
    path("api/v1/interview/answer/<uuid:answer_id>", views.interview_answer_status, name="interview_answer_status"),
    path("api/v1/interview/history", views.interview_history, name="interview_history"),
    # Dashboard endpoint
    path("api/v1/dashboard", views.dashboard, name="dashboard"),
]
