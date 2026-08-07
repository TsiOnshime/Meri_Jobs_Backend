from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("services/health", views.service_health, name="service_health"),
    
    # Authentication endpoints (proxied to users service)
    path("auth/register", views.auth_register, name="auth_register"),
    path("auth/login", views.auth_login, name="auth_login"),
    path("auth/refresh", views.auth_refresh, name="auth_refresh"),
    path("auth/logout", views.auth_logout, name="auth_logout"),
    path("auth/me", views.auth_me, name="auth_me"),
    path("auth/change-password", views.auth_change_password, name="auth_change_password"),
    
    # Profile management endpoints (proxied to users service)
    path("auth/profile/", views.profile, name="profile"),
    
    # CV Parser endpoints (proxied to cv-parser service)
    path("cv/upload", views.cv_upload, name="cv_upload"),
    path("cv/<uuid:cv_id>/status", views.cv_status, name="cv_status"),
    path("cv/<uuid:cv_id>", views.cv_update, name="cv_update"),
    path("cv/<uuid:cv_id>/export", views.cv_export, name="cv_export"),
    path("cv/<uuid:cv_id>/suggestions/accept", views.cv_suggestions_accept, name="cv_suggestions_accept"),
    path("cv/<uuid:cv_id>/suggestions/accept-all", views.cv_suggestions_accept_all, name="cv_suggestions_accept_all"),
    path("cv/<uuid:cv_id>/suggestions/undo", views.cv_suggestions_undo, name="cv_suggestions_undo"),
    
    # Matching Engine endpoints
    path("matches/<uuid:cv_id>", views.matches_list, name="matches_list"),
    path("matches/<uuid:cv_id>/<uuid:job_id>", views.match_detail, name="match_detail"),
    
    # Interview Prep endpoints (proxied to interview-prep service)
    path("interview/session", views.interview_session, name="interview_session"),
    path("interview/session/<uuid:session_id>/answer", views.interview_answer, name="interview_answer"),
    path("interview/answer/<uuid:answer_id>", views.interview_answer_feedback, name="interview_answer_feedback"),
    path("interview/history", views.interview_history, name="interview_history"),
    
    # Dashboard endpoint
    path("dashboard", views.dashboard, name="dashboard"),
]
