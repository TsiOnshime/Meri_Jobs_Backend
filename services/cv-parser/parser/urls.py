from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("cv/upload", views.CVUploadView.as_view(), name="cv-upload"),
    path("cv/<uuid:cv_id>/status", views.CVStatusView.as_view(), name="cv-status"),
    path("cv/<uuid:cv_id>", views.CVEditView.as_view(), name="cv-edit"),
    path("cv/<uuid:cv_id>/export", views.CVExportView.as_view(), name="cv-export"),
    path(
        "cv/<uuid:cv_id>/suggestions/accept",
        views.SuggestionAcceptView.as_view(),
        name="suggestion-accept",
    ),
    path(
        "cv/<uuid:cv_id>/suggestions/accept-all",
        views.SuggestionAcceptAllView.as_view(),
        name="suggestion-accept-all",
    ),
    path(
        "cv/<uuid:cv_id>/suggestions/undo",
        views.SuggestionUndoView.as_view(),
        name="suggestion-undo",
    ),
]