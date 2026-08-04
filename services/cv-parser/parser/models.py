import uuid

from django.db import models


class CV(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        NEEDS_REVIEW = "needs_review", "Needs review"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    original_filename = models.CharField(max_length=255)
    storage_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=10, choices=[("pdf", "PDF"), ("docx", "DOCX")])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class CVScore(models.Model):
    overall = models.IntegerField()
    completeness = models.IntegerField()
    keyword_relevance = models.IntegerField()
    clarity = models.IntegerField()
    computed_at = models.DateTimeField(auto_now=True)
    cv = models.OneToOneField("parser.CV", related_name="score", on_delete=models.CASCADE)


class CVSuggestion(models.Model):
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
    type = models.CharField(max_length=30, choices=Type.choices)
    field_reference = models.CharField(max_length=255)
    suggestion_text = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    edited_text = models.TextField(blank=True, null=True)
    previous_status = models.CharField(max_length=20, blank=True, default="")
    previous_text = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)
    cv = models.ForeignKey("parser.CV", related_name="suggestions", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-updated_at"]

    def apply_action(self, action, edited_text=None):
        if action == "accept":
            self.status = self.Status.ACCEPTED
        elif action == "reject":
            self.status = self.Status.REJECTED
        elif action == "edit":
            self.status = self.Status.EDITED
            if edited_text is not None:
                self.edited_text = edited_text
                self.suggestion_text = edited_text
        else:
            raise ValueError(f"Unsupported action: {action}")

        if not self.previous_status:
            self.previous_status = self.Status.PENDING
        if not self.previous_text:
            self.previous_text = self.suggestion_text

        self.save()

    def undo(self):
        if not self.previous_status and not self.previous_text:
            return False

        self.status = self.previous_status or self.Status.PENDING
        if self.previous_text:
            self.suggestion_text = self.previous_text
        self.previous_status = ""
        self.previous_text = ""
        self.save(update_fields=["status", "suggestion_text", "previous_status", "previous_text", "updated_at"])
        return True


class ParsedCV(models.Model):
    name = models.CharField(max_length=255, blank=True, default="")
    email = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    professional_summary = models.TextField(blank=True, null=True)
    education = models.JSONField(blank=True, default=list)
    experience = models.JSONField(blank=True, default=list)
    skills = models.JSONField(blank=True, default=list)
    certifications = models.JSONField(blank=True, default=list)
    raw_text = models.TextField(blank=True, default="")
    parser_version = models.CharField(max_length=50, default="v1")
    confidence_score = models.FloatField(default=0.0)
    flagged_sections = models.JSONField(blank=True, default=list)
    experience_years = models.IntegerField(default=0)
    role_category = models.CharField(max_length=100, default="unspecified")
    cv = models.OneToOneField("parser.CV", related_name="parsed", on_delete=models.CASCADE)


class ParseFailureLog(models.Model):
    error_type = models.CharField(max_length=100)
    error_detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    cv = models.ForeignKey("parser.CV", related_name="failure_logs", on_delete=models.CASCADE)
