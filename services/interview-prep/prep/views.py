import json
import uuid

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Answer, InterviewSession, Question
from .tasks import _mark_session_complete_if_done, evaluate_answer


def health(request):
    """Liveness check -- used by docker-compose / orchestration."""
    return JsonResponse({"status": "ok", "service": "interview-prep"})


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _correlation_id(request):
    return request.META.get("HTTP_X_CORRELATION_ID") or str(uuid.uuid4())


def _error(code, message, status, correlation_id):
    """Standard error envelope, matching Frontend_API_Design section 06.

    api-gateway's http_client just forwards our body + status code
    verbatim, so we're the ones who actually have to produce this shape,
    not just the gateway.
    """
    return JsonResponse(
        {"error": {"code": code, "message": message}, "correlation_id": correlation_id},
        status=status,
    )


def _question_payload(session, question):
    """Shape a Question for the frontend. Never includes correct_option."""
    payload = {
        "session_id": str(session.id),
        "question_id": str(question.id),
        "round_number": question.round_number,
        "total_rounds": session.total_rounds,
        "question": question.text,
        "difficulty": question.difficulty,
        "question_type": question.question_type,
        "time_limit": question.time_limit,
    }
    if question.question_type == "multiple_choice":
        payload["options"] = question.options
    return payload


def _next_question_payload(session):
    """The lowest-round_number question that doesn't have an Answer yet.

    All `total_rounds` questions were generated and persisted up front at
    session creation (one LLM call, see generation/questions.py), so
    "the next question" is always just a DB read -- never a fresh LLM
    call -- which is what lets us hand it back inline on the answer
    endpoints below instead of making the frontend poll a separate
    "next question" endpoint.
    """
    question = (
        session.questions.filter(answer__isnull=True).order_by("round_number").first()
    )
    return _question_payload(session, question) if question else None


# ---------------------------------------------------------------------------
# POST /internal/interview/session
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def create_session(request):
    correlation_id = _correlation_id(request)
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _error("VALIDATION_ERROR", "Invalid JSON body", 400, correlation_id)

    user_id = data.get("user_id")
    job_id = data.get("job_id")
    if not user_id or not job_id:
        return _error(
            "VALIDATION_ERROR", "user_id and job_id are required", 400, correlation_id
        )

    focus_area = data.get("focus_area", "") or ""
    job_title = data.get("job_title", "") or ""

    # Isolated import: keeps the Gemini SDK/API-key requirement out of the
    # module import path for every other view (same reasoning tasks.py
    # uses for generate_feedback).
    from .generation.job_cache import pop_cached_questions
    from .generation.questions import generate_questions

    # match_found_consumer may have already pre-generated a set for this
    # exact (job_id, focus_area) pair -- if so, use it instead of paying
    # for another Gemini call. Redis being unreachable shouldn't block
    # session creation, so any cache failure just falls through to a live
    # generate_questions() call below.
    try:
        generated = pop_cached_questions(job_id, focus_area)
    except Exception:
        generated = None

    if not generated:
        try:
            generated = generate_questions(
                job_title=job_title, focus_area=focus_area, count=10
            )
        except Exception:
            return _error(
                "SERVICE_UNAVAILABLE",
                "Couldn't generate interview questions right now, try again shortly",
                503,
                correlation_id,
            )

    if not generated:
        return _error(
            "SERVICE_UNAVAILABLE",
            "Question generation returned no questions",
            503,
            correlation_id,
        )

    session = InterviewSession.objects.create(
        user_id=user_id,
        job_id=job_id,
        job_title=job_title,
        focus_area=focus_area,
        total_rounds=len(generated),
    )
    Question.objects.bulk_create(
        Question(session=session, round_number=i + 1, **q)
        for i, q in enumerate(generated)
    )

    first_question = session.questions.order_by("round_number").first()
    return JsonResponse(_question_payload(session, first_question), status=201)


# ---------------------------------------------------------------------------
# POST /internal/interview/{session_id}/answer
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def submit_answer(request, session_id):
    correlation_id = _correlation_id(request)
    try:
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        return _error("NOT_FOUND", "Session not found", 404, correlation_id)

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _error("VALIDATION_ERROR", "Invalid JSON body", 400, correlation_id)

    question = (
        session.questions.filter(answer__isnull=True).order_by("round_number").first()
    )
    if question is None:
        return _error(
            "VALIDATION_ERROR", "This session has no pending question left", 400,
            correlation_id,
        )

    time_taken = data.get("time_taken", 0)
    answer = Answer(question=question, time_taken=time_taken)

    if question.question_type == "multiple_choice":
        selected_option = data.get("selected_option")
        if not isinstance(selected_option, int):
            return _error(
                "VALIDATION_ERROR",
                "selected_option (integer index into the question's options) is required",
                400,
                correlation_id,
            )

        from .scoring import grade_multiple_choice

        result = grade_multiple_choice(question, selected_option)
        answer.selected_option = selected_option
        answer.score = result["score"]
        answer.strengths = result["strengths"]
        answer.improvements = result["improvements"]
        answer.status = "completed"
        answer.completed_at = timezone.now()
        answer.save()
        _mark_session_complete_if_done(session)
    else:
        answer.answer_text = data.get("answer", "") or ""
        answer.status = "processing"
        answer.save()
        evaluate_answer.delay(str(answer.id))

    session.refresh_from_db()
    return JsonResponse(
        {
            "answer_id": str(answer.id),
            "status": answer.status,
            "message": "Answer submitted for evaluation"
            if answer.status == "processing"
            else "Answer graded",
            "session_status": session.status,
            "next_question": _next_question_payload(session),
        },
        status=202,
    )


# ---------------------------------------------------------------------------
# GET /internal/interview/answer/{answer_id}
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def answer_status(request, answer_id):
    correlation_id = _correlation_id(request)
    try:
        answer = Answer.objects.select_related("question", "question__session").get(
            id=answer_id
        )
    except Answer.DoesNotExist:
        return _error("NOT_FOUND", "Answer not found", 404, correlation_id)

    body = {"answer_id": str(answer.id), "status": answer.status}

    if answer.status == "completed":
        feedback = {
            "score": answer.score,
            "strengths": answer.strengths,
            "improvements": answer.improvements,
            "suggested_answer": answer.suggested_answer,
        }
        if answer.question.question_type == "multiple_choice":
            feedback["correct_option"] = answer.question.correct_option
            feedback["selected_option"] = answer.selected_option
        body["feedback"] = feedback
        body["next_question"] = _next_question_payload(answer.question.session)
        body["session_status"] = answer.question.session.status

    return JsonResponse(body, status=200)


# ---------------------------------------------------------------------------
# GET /internal/interview/history/{user_id}
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def history(request, user_id):
    correlation_id = _correlation_id(request)

    try:
        limit = int(request.GET.get("limit", 10))
        offset = int(request.GET.get("offset", 0))
    except ValueError:
        return _error(
            "VALIDATION_ERROR", "limit and offset must be integers", 400, correlation_id
        )

    job_id = request.GET.get("job_id")

    from django.db.models import Avg

    sessions_qs = InterviewSession.objects.filter(user_id=user_id)
    if job_id:
        sessions_qs = sessions_qs.filter(job_id=job_id)

    total_sessions = sessions_qs.count()
    page = list(sessions_qs[offset : offset + limit])

    sessions_payload = []
    for session in page:
        agg = Answer.objects.filter(
            question__session=session, status="completed"
        ).aggregate(avg=Avg("score"))
        sessions_payload.append(
            {
                "session_id": str(session.id),
                "job_id": str(session.job_id),
                "job_title": session.job_title,
                "date": session.created_at.isoformat(),
                "average_score": round(agg["avg"], 1) if agg["avg"] is not None else None,
                "questions_answered": session.rounds_completed,
            }
        )

    overall = Answer.objects.filter(
        question__session__in=sessions_qs, status="completed"
    ).aggregate(avg=Avg("score"))
    overall_avg = round(overall["avg"], 1) if overall["avg"] is not None else None

    # Crude strength/weakness signal: average score per focus_area across
    # this user's sessions. Good enough for a v1 dashboard card; a real
    # per-topic breakdown would need question-level tagging we don't have.
    area_rows = (
        sessions_qs.exclude(focus_area="")
        .values("focus_area")
        .annotate(avg_score=Avg("questions__answer__score"))
    )
    strong_areas = sorted(
        (r["focus_area"] for r in area_rows if (r["avg_score"] or 0) >= 7),
        key=lambda _: 0,
    )[:5]
    weak_areas = [
        r["focus_area"] for r in area_rows if r["avg_score"] is not None and r["avg_score"] < 7
    ][:5]

    return JsonResponse(
        {
            "sessions": sessions_payload,
            "aggregated_stats": {
                "total_sessions": total_sessions,
                "average_score": overall_avg,
                "strong_areas": strong_areas,
                "weak_areas": weak_areas,
            },
        },
        status=200,
    )