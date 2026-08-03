import uuid

from django.db import models


class InterviewSession(models.Model):
    """One practice interview session, started against a specific job.

    job_id is a reference into matching-engine's Job table -- we never join
    across services, so we just store the id (+ a denormalized job_title we
    pick up later, e.g. once the match_found consumer is wired up).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # api-gateway is the one caller allowed to reach this service directly
    # (see docs/architecture.md), and it already attaches the caller's
    # user_id when it proxies POST /interview/session and builds the URL
    # for GET /interview/history/{user_id}. We store it so /history can
    # actually scope results to one account instead of returning every
    # user's sessions.
    user_id = models.UUIDField(db_index=True)
    job_id = models.UUIDField()
    job_title = models.CharField(max_length=255, blank=True, default="")
    focus_area = models.CharField(max_length=100, blank=True, default="")
    total_rounds = models.PositiveSmallIntegerField(default=10)
    status = models.CharField(
        max_length=15,
        choices=[("in_progress", "In progress"), ("completed", "Completed")],
        default="in_progress",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session {self.id} ({self.focus_area or 'general'})"

    @property
    def rounds_completed(self):
        return self.questions.filter(answer__status="completed").count()

    @property
    def is_complete(self):
        return self.rounds_completed >= self.total_rounds


class Question(models.Model):

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    TYPE_CHOICES = [
        ("open_ended", "Open ended"),
        ("multiple_choice", "Multiple choice"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        InterviewSession, on_delete=models.CASCADE, related_name="questions"
    )
    round_number = models.PositiveSmallIntegerField(
        help_text="1-indexed position of this question within the session's rounds"
    )
    text = models.TextField()
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default="medium"
    )
    question_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default="open_ended"
    )
    # Only populated when question_type == "multiple_choice".
    options = models.JSONField(null=True, blank=True, default=None)
    correct_option = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        default=None,
        help_text="Index into `options`. Never serialize this to the frontend before the answer is submitted.",
    )
    time_limit = models.PositiveIntegerField(help_text="Seconds allowed to answer")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["round_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "round_number"], name="unique_round_per_session"
            )
        ]

    def __str__(self):
        return f"Question {self.round_number}/{self.session.total_rounds} for session {self.session_id}"


class Answer(models.Model):
    """A submitted answer to a Question, evaluated asynchronously (Celery)."""

    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField(
        Question, on_delete=models.CASCADE, related_name="answer"
    )
    # For open_ended questions. Blank for multiple_choice.
    answer_text = models.TextField(blank=True, default="")
    # For multiple_choice questions: index into question.options. Null for open_ended.
    selected_option = models.PositiveSmallIntegerField(null=True, blank=True)
    time_taken = models.PositiveIntegerField(help_text="Seconds the candidate took")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="processing"
    )

    # Populated once evaluation completes.
    score = models.FloatField(null=True, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    improvements = models.JSONField(default=list, blank=True)
    suggested_answer = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Answer {self.id} ({self.status})"

    @property
    def session(self):
        return self.question.session