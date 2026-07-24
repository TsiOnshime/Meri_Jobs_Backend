import uuid

from django.db import models


class CV(models.Model):
    """One uploaded CV and its lifecycle status.

    status flow:
        pending -> processing -> complete
                              -> needs_review   (low parser confidence)
                              -> failed         (corrupted file)
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        NEEDS_REVIEW = "needs_review", "Needs review"
        FAILED = "failed", "Failed"

    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        DOCX = "docx", "DOCX"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    original_filename = models.CharField(max_length=255)
    storage_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CV({self.id}, {self.status})"


class ParsedCV(models.Model):
    """The structured result of parsing. One-to-one with CV."""

    cv = models.OneToOneField(CV, on_delete=models.CASCADE, related_name="parsed")

    name = models.CharField(max_length=255, blank=True, default="")
    email = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    professional_summary = models.TextField(blank=True, null=True)

    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)  # normalized skill strings
    certifications = models.JSONField(default=list, blank=True)
    experience_years = models.IntegerField(default=0)
    role_category = models.CharField(max_length=100, default="unspecified")

    raw_text = models.TextField(blank=True, default="")
    parser_version = models.CharField(max_length=50, default="v1")

    confidence_score = models.FloatField(default=0.0)  # 0.0 - 1.0
    flagged_sections = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"ParsedCV(cv={self.cv_id}, confidence={self.confidence_score})"


class CVScore(models.Model):
    """The 0-100 score, broken into 3 sub-scores."""

    cv = models.OneToOneField(CV, on_delete=models.CASCADE, related_name="score")
    overall = models.IntegerField()
    completeness = models.IntegerField()
    keyword_relevance = models.IntegerField()
    clarity = models.IntegerField()
    computed_at = models.DateTimeField(auto_now=True)


class CVSuggestion(models.Model):
    """One optimization suggestion the user can accept/reject/edit."""

    class Type(models.TextChoices):
        MISSING_KEYWORD = "missing_keyword", "Missing keyword"
        WEAK_BULLET = "weak_bullet", "Weak bullet"
        UNQUANTIFIED = "unquantified", "Unquantified achievement"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        EDITED = "edited", "Edited"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="suggestions")
    type = models.CharField(max_length=30, choices=Type.choices)
    field_reference = models.CharField(max_length=100)
    suggestion_text = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    edited_text = models.TextField(blank=True, null=True)

    # Undo support: remember what status/text were before the last action,
    # so /suggestions/undo has something to revert to.
    previous_status = models.CharField(max_length=20, blank=True, default="")
    previous_text = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def apply_action(self, action: str, edited_text: str | None = None):
        self.previous_status = self.status
        self.previous_text = self.edited_text or ""
        if action == "accept":
            self.status = self.Status.ACCEPTED
        elif action == "reject":
            self.status = self.Status.REJECTED
        elif action == "edit":
            self.status = self.Status.EDITED
            self.edited_text = edited_text
        else:
            raise ValueError(f"Unknown action: {action}")
        self.save()

    def undo(self):
        if not self.previous_status:
            return False
        self.status = self.Status.PENDING
        self.edited_text = self.previous_text or None
        self.previous_status = ""
        self.previous_text = ""
        self.save()
        return True


class ParseFailureLog(models.Model):
    """Corrupted/unusual files must be logged, never silently dropped."""

    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="failure_logs")
    error_type = models.CharField(max_length=100)
    error_detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)