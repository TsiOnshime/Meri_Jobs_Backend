import os
import uuid

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exporters import build_cv_pdf
from .models import CV, CVSuggestion
from .tasks import parse_cv_task

ALLOWED_EXTENSIONS = {".pdf": "pdf", ".docx": "docx"}


def health(request):
    """Liveness check -- used by docker-compose / orchestration."""
    return JsonResponse({"status": "ok", "service": "cv-parser"})


def _error(message, detail="", code=status.HTTP_400_BAD_REQUEST):
    return Response({"error": message, "detail": detail}, status=code)


class CVUploadView(APIView):
    """POST /internal/cv/upload -- returns immediately, parsing happens async."""

    def post(self, request):
        file_obj = request.FILES.get("file")
        user_id = request.data.get("user_id")

        if not file_obj or not user_id:
            return _error("Missing file or user_id")

        ext = os.path.splitext(file_obj.name)[1].lower()
        file_type = ALLOWED_EXTENSIONS.get(ext)
        if not file_type:
            return _error("Unsupported file type", detail="Only .pdf and .docx are accepted")

        if file_obj.size > settings.MAX_UPLOAD_SIZE_BYTES:
            return _error("File too large")

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        storage_path = os.path.join(settings.MEDIA_ROOT, f"{uuid.uuid4()}{ext}")
        with open(storage_path, "wb") as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        print("CV-PARSER saved file:", storage_path, "size=", os.path.getsize(storage_path), flush=True)
        cv = CV.objects.create(
            user_id=user_id,
            original_filename=file_obj.name,
            storage_path=storage_path,
            file_type=file_type,
            status=CV.Status.PENDING,
        )

        parse_cv_task.delay(str(cv.id))  # async -- do not wait for this

        return Response(
            {"cv_id": str(cv.id), "status": cv.status},
            status=status.HTTP_202_ACCEPTED,
        )


class CVStatusView(APIView):
    """GET /internal/cv/{id}/status -- poll target for the frontend."""

    def get(self, request, cv_id):
        try:
            cv = CV.objects.select_related("parsed", "score").get(id=cv_id)
        except CV.DoesNotExist:
            return _error("CV not found", code=status.HTTP_404_NOT_FOUND)

        parsed = getattr(cv, "parsed", None)
        score = getattr(cv, "score", None)

        data = {
            "cv_id": str(cv.id),
            "status": cv.status,
            "uploaded_at": cv.uploaded_at,
            "updated_at": cv.updated_at,
            "score": {
                "overall": score.overall,
                "completeness": score.completeness,
                "keyword_relevance": score.keyword_relevance,
                "clarity": score.clarity,
            } if score else None,
            "parsed": {
                "name": parsed.name,
                "email": parsed.email,
                "phone": parsed.phone,
                "professional_summary": parsed.professional_summary,
                "education": parsed.education,
                "experience": parsed.experience,
                "skills": parsed.skills,
                "certifications": parsed.certifications,
                "confidence_score": parsed.confidence_score,
            } if parsed else None,
            "suggestions": [
                {
                    "suggestion_id": str(s.id),
                    "type": s.type,
                    "field_reference": s.field_reference,
                    "suggestion_text": s.suggestion_text,
                    "status": s.status,
                }
                for s in cv.suggestions.all()
            ],
            "flagged_sections": parsed.flagged_sections if parsed else [],
        }
        return Response(data)
class CVEditView(APIView):
    """PATCH /internal/cv/{id} -- FR1.4, manual correction of parsed fields."""

    EDITABLE_FIELDS = [
        "name", "email", "phone", "professional_summary",
        "education", "experience", "skills", "certifications",
    ]

    def patch(self, request, cv_id):
        try:
            cv = CV.objects.select_related("parsed").get(id=cv_id)
        except CV.DoesNotExist:
            return _error("CV not found", code=status.HTTP_404_NOT_FOUND)

        if cv.status in (CV.Status.PENDING, CV.Status.PROCESSING):
            return _error("CV has not finished parsing yet", code=status.HTTP_409_CONFLICT)

        parsed = getattr(cv, "parsed", None)
        if parsed is None:
            return _error("Nothing parsed yet for this CV", code=status.HTTP_409_CONFLICT)

        changed = []
        for field in self.EDITABLE_FIELDS:
            if field in request.data:
                setattr(parsed, field, request.data[field])
                changed.append(field)
        parsed.save()

        if cv.status == CV.Status.NEEDS_REVIEW:
            still_flagged = [f for f in parsed.flagged_sections if f not in changed]
            parsed.flagged_sections = still_flagged
            parsed.save(update_fields=["flagged_sections"])
            if not still_flagged:
                cv.status = CV.Status.COMPLETE
                cv.save(update_fields=["status", "updated_at"])

        return Response({
            "name": parsed.name,
            "email": parsed.email,
            "phone": parsed.phone,
            "professional_summary": parsed.professional_summary,
            "education": parsed.education,
            "experience": parsed.experience,
            "skills": parsed.skills,
            "certifications": parsed.certifications,
            "confidence_score": parsed.confidence_score,
        })


class CVExportView(APIView):
    """GET /internal/cv/{id}/export -- FR2.4."""
    authentication_classes = []  # Bypass authentication for internal service
    permission_classes = []  # Allow any request with internal token

    def get(self, request, cv_id):
        try:
            cv = CV.objects.select_related("parsed").get(id=cv_id)
        except CV.DoesNotExist:
            return _error("CV not found", code=status.HTTP_404_NOT_FOUND)

        if cv.status in (CV.Status.PENDING, CV.Status.PROCESSING):
            return _error(
                "CV is still being processed -- nothing to export yet",
                code=status.HTTP_409_CONFLICT,
            )

        parsed = getattr(cv, "parsed", None)
        if parsed is None:
            return _error("Nothing to export", code=status.HTTP_409_CONFLICT)

        pdf_bytes = build_cv_pdf(cv, parsed)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{cv.id}-optimized.pdf"'
        return response


class SuggestionAcceptView(APIView):
    """POST /internal/cv/{id}/suggestions/accept -- FR2.2."""

    def post(self, request, cv_id):
        suggestion_id = request.data.get("suggestion_id")
        action = request.data.get("action")
        edited_text = request.data.get("edited_text")

        if not suggestion_id or action not in ("accept", "reject", "edit"):
            return _error("suggestion_id and a valid action are required")
        if action == "edit" and not edited_text:
            return _error("edited_text is required when action=edit")

        try:
            suggestion = CVSuggestion.objects.get(id=suggestion_id, cv_id=cv_id)
        except CVSuggestion.DoesNotExist:
            return _error("Suggestion not found", code=status.HTTP_404_NOT_FOUND)

        suggestion.apply_action(action, edited_text)
        return Response({
            "suggestion_id": str(suggestion.id),
            "type": suggestion.type,
            "field_reference": suggestion.field_reference,
            "suggestion_text": suggestion.suggestion_text,
            "status": suggestion.status,
        })


class SuggestionAcceptAllView(APIView):
    """POST /internal/cv/{id}/suggestions/accept-all -- UI addition, not in the FR doc."""

    def post(self, request, cv_id):
        if not CV.objects.filter(id=cv_id).exists():
            return _error("CV not found", code=status.HTTP_404_NOT_FOUND)

        pending = CVSuggestion.objects.filter(cv_id=cv_id, status=CVSuggestion.Status.PENDING)
        for s in pending:
            s.apply_action("accept")

        return Response([
            {
                "suggestion_id": str(s.id),
                "type": s.type,
                "field_reference": s.field_reference,
                "suggestion_text": s.suggestion_text,
                "status": s.status,
            }
            for s in pending
        ])


class SuggestionUndoView(APIView):
    """POST /internal/cv/{id}/suggestions/undo -- UI addition, not in the FR doc."""

    def post(self, request, cv_id):
        suggestion_id = request.data.get("suggestion_id")

        qs = CVSuggestion.objects.filter(cv_id=cv_id)
        target = (
            qs.filter(id=suggestion_id).first() if suggestion_id
            else qs.exclude(previous_status="").order_by("-updated_at").first()
        )

        if not target or not target.undo():
            return _error("Nothing to undo", code=status.HTTP_404_NOT_FOUND)

        return Response({
            "suggestion_id": str(target.id),
            "type": target.type,
            "field_reference": target.field_reference,
            "suggestion_text": target.suggestion_text,
            "status": target.status,
        })