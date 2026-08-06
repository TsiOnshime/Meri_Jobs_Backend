from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("session", views.CreateSessionView.as_view(), name="create-session"),
    path("session/<uuid:session_id>/questions", views.GetQuestionsView.as_view(), name="get-questions"),
    path("question/<uuid:question_id>/answer", views.SubmitAnswerView.as_view(), name="submit-answer"),
    path("answer/<uuid:answer_id>/feedback", views.GetFeedbackView.as_view(), name="get-feedback"),
]
