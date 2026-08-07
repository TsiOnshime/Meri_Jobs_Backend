import uuid
from django.db import models


class Session(models.Model):
    """Interview session for a CV and job pair."""
    STATUS_CHOICES = [
        ("created", "Created"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv_id = models.UUIDField()
    job_id = models.UUIDField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "interview_session"
        indexes = [
            models.Index(fields=["cv_id", "job_id"]),
        ]
    
    def __str__(self):
        return f"Session({self.id}, {self.status})"


class Question(models.Model):
    """Interview question for a session."""
    CATEGORY_CHOICES = [
        ("technical", "Technical"),
        ("behavioral", "Behavioral"),
        ("general", "General"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = "interview_question"
        ordering = ["order"]
    
    def __str__(self):
        return f"Question({self.id}, {self.category})"


class Answer(models.Model):
    """User's answer to an interview question."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    user_answer = models.TextField()
    feedback = models.TextField(blank=True, null=True)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "interview_answer"
    
    def __str__(self):
        return f"Answer({self.id}, score={self.score})"
