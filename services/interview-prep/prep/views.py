import uuid
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from .models import Session, Question, Answer


def health(request):
    """Liveness check -- used by docker-compose / orchestration."""
    return JsonResponse({"status": "ok", "service": "interview-prep"})


class CreateSessionView(APIView):
    """Create a new interview session for a CV and job pair."""
    
    def post(self, request):
        try:
            data = request.data
            cv_id = data.get("cv_id")
            job_id = data.get("job_id")
            
            if not cv_id or not job_id:
                return JsonResponse(
                    {"error": {"code": "bad_request", "message": "cv_id and job_id are required"}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            session = Session.objects.create(
                cv_id=uuid.UUID(cv_id),
                job_id=uuid.UUID(job_id),
                status="created"
            )
            
            # Generate some sample questions (placeholder - would use LLM in production)
            sample_questions = [
                {"question_text": "Tell me about yourself.", "category": "general", "order": 1},
                {"question_text": "What experience do you have with Python?", "category": "technical", "order": 2},
                {"question_text": "Describe a challenging project you worked on.", "category": "behavioral", "order": 3},
            ]
            
            for q_data in sample_questions:
                Question.objects.create(
                    session=session,
                    question_text=q_data["question_text"],
                    category=q_data["category"],
                    order=q_data["order"]
                )
            
            session.status = "in_progress"
            session.save()
            
            return JsonResponse({
                "session_id": str(session.id),
                "cv_id": str(session.cv_id),
                "job_id": str(session.job_id),
                "status": session.status,
                "question_count": len(sample_questions)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return JsonResponse(
                {"error": {"code": "server_error", "message": str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetQuestionsView(APIView):
    """Get all questions for a session."""
    
    def get(self, request, session_id):
        try:
            session = Session.objects.get(id=session_id)
            questions = session.questions.all()
            
            questions_data = [
                {
                    "question_id": str(q.id),
                    "question_text": q.question_text,
                    "category": q.category,
                    "order": q.order
                }
                for q in questions
            ]
            
            return JsonResponse({
                "session_id": str(session.id),
                "status": session.status,
                "questions": questions_data
            })
            
        except Session.DoesNotExist:
            return JsonResponse(
                {"error": {"code": "not_found", "message": "Session not found"}},
                status=status.HTTP_404_NOT_FOUND
            )


class SubmitAnswerView(APIView):
    """Submit an answer to a question."""
    
    def post(self, request, question_id):
        try:
            data = request.data
            user_answer = data.get("user_answer")
            
            if not user_answer:
                return JsonResponse(
                    {"error": {"code": "bad_request", "message": "user_answer is required"}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            question = Question.objects.get(id=question_id)
            
            # Check if answer already exists
            existing_answer = Answer.objects.filter(question=question).first()
            if existing_answer:
                existing_answer.user_answer = user_answer
                existing_answer.save()
                answer = existing_answer
            else:
                answer = Answer.objects.create(
                    question=question,
                    user_answer=user_answer,
                    score=0  # Placeholder - would use LLM to score
                )
            
            return JsonResponse({
                "answer_id": str(answer.id),
                "question_id": str(question.id),
                "score": answer.score
            }, status=status.HTTP_201_CREATED)
            
        except Question.DoesNotExist:
            return JsonResponse(
                {"error": {"code": "not_found", "message": "Question not found"}},
                status=status.HTTP_404_NOT_FOUND
            )


class GetFeedbackView(APIView):
    """Get feedback for an answer."""
    
    def get(self, request, answer_id):
        try:
            answer = Answer.objects.get(id=answer_id)
            
            # Generate placeholder feedback (would use LLM in production)
            if not answer.feedback:
                answer.feedback = "Good answer! Consider adding more specific examples."
                answer.score = 75
                answer.save()
            
            return JsonResponse({
                "answer_id": str(answer.id),
                "question_id": str(answer.question.id),
                "user_answer": answer.user_answer,
                "feedback": answer.feedback,
                "score": answer.score
            })
            
        except Answer.DoesNotExist:
            return JsonResponse(
                {"error": {"code": "not_found", "message": "Answer not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
