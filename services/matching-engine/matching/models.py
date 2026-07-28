import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

class Skill(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        db_table = "skill"
        
    def __str__(self):
        return self.name

class SkillAlias(models.Model):
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4,
        editable=False
    )
    alias_name = models.CharField(max_length=100, unique=True)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="aliases"
    )
    
    class Meta:
        db_table = "skill_alias"
    
    def __str__(self):
        return f"{self.alias_name} -> {self.skill.name}"
    
class CV(models.Model):
    SENIORITY_CHOICES = [
        ("junior", "Junior"),
        ("mid", "Mid"), 
        ("senior", "Senior"),
        ("lead", "Lead"),
    ]
    
    cv_id = models.UUIDField(
        primary_key=True, 
        editable=False
    )
    skill_ids = ArrayField(
        models.UUIDField(), 
        default=list,
        help_text="Canonical Skill IDs, already resolved. Never raw skill strings."
    
    )
    experience_years = models.FloatField()
    seniority = models.CharField(max_length=10, choices=SENIORITY_CHOICES)
    role_category = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now = True)
    
    class Meta:
        db_table = "cv"
        indexes = [
            models.Index(fields=["role_category"])
        ]
class Job(models.Model):
    SENIORITY_CHOICES = CV.SENIORITY_CHOICES
    
    job_id = models.UUIDField(
        primary_key=True,
        editable=False
    )
    skill_ids = ArrayField(
        models.UUIDField(), 
        default=list,
        help_text="Canonical Skill IDs, already resolved. Single list"
    )
    min_experience = models.FloatField() 
    seniority_level = models.CharField(
        max_length=10, 
        choices=SENIORITY_CHOICES
    )
    role_category = models.CharField(max_length=100)
    location = models.CharField(max_length = 100)
    source_url = models.URLField(
        max_length=500, 
        help_text="Direct link to the original listing"
    )
    ingested_at = models.DateTimeField()
    
    class Meta:
        db_table = "job"
        indexes = [
            models.Index(fields=["role_category"])
        ]

    def __str__(self):
        return f"Job({self.job_id})"
    
class Match(models.Model):
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4,
        editable=False
    )
    cv = models.ForeignKey(
        CV, 
        on_delete=models.CASCADE,
        related_name="matches", 
        db_column="cv_id"
    )
    job = models.ForeignKey(
        Job, 
        on_delete=models.CASCADE,
        related_name="matches",
        db_column="job_id"
    )
    overall_score=models.PositiveSmallIntegerField()
    breakdown=models.JSONField()
    computed_at=models.DateField(auto_now=True)
    
    class Meta: 
        db_table = "match"
        constraints = [
            models.UniqueConstraint(
                fields=["cv", "job"],
                name="unique_cv_job_match",
            )
        ]
        indexes = [
            models.Index(fields=["cv", "-overall_score"])
        ]
    
    def __str__(self):
        return f"Match(cv={self.cv_id}, job={self.job_id}, score={self.overall_score})"