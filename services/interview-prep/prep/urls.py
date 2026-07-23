from django.urls import path

from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    # Paths mirror api-gateway/gateway/views.py's hardcoded INTERVIEW_PREP_URL
    # routes exactly -- gateway is already coded against these, so they
    # aren't ours to redesign independently.
    path("interview/session", views.create_session, name="interview_session"),
    path(
        "interview/<uuid:session_id>/answer",
        views.submit_answer,
        name="interview_answer",
    ),
    path(
        "interview/answer/<uuid:answer_id>",
        views.answer_status,
        name="interview_answer_status",
    ),
    path("interview/history/<uuid:user_id>", views.history, name="interview_history"),
]