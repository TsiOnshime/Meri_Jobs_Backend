"""Consumes job.ingested: resolves skills, filters CVs, scores."""
import logging
from matching.models import CV, Job, Match
from matching.skills.resolve import resolve_skills
from matching.scoring.gate import passes_gate
from matching.scoring.weighted_score import compute_score
from matching.publishers.match_found import publish_match_found
from matching.publishers.match_invalidated import publish_match_invalidated

logger = logging.getLogger(__name__)


def handle_job_ingested(event: dict) -> None:
    job_id = event["job_id"]
    
    is_reingest = Job.objects.filter(job_id=job_id).exists()
    
    previously_matched_cv_ids = set()
    
    if is_reingest:
        previously_matched_cv_ids = set(
            Match.objects.filter(job=job_id).values_list("cv_id", flat=True)
        )
        
    resolved_skill_ids = resolve_skills(event["required_skills"])
    
    job, _ = Job.objects.update_or_create(
        job_id=job_id,
        defaults={
            "skill_ids": resolved_skill_ids,
            "min_experience": event["min_experience"],
            "seniority_level": event["seniority_level"],
            "role_category": event["role_category"],
            "location": event["location"],
            "source_url": event["source"],
            "ingested_at": event["timestamp"]
        },
    )
    
    candidate_cvs = CV.objects.filter(role_category=job.role_category)
    
    newly_qualified_cv_ids = set()
    
    for cv in candidate_cvs:
        gate_result = passes_gate(cv,job)
        if not gate_result.passed:
            continue
        overall_score, breakdown = compute_score(cv, job, gate_result)
        
        Match.objects.update_or_create(
            cv=cv,
            job=job,
            defaults={"overall_score": overall_score, "breakdown": breakdown},
        )
        
        newly_qualified_cv_ids.add(cv.cv_id)
        
        publish_match_found(cv, job, overall_score, breakdown)
        
    if is_reingest:
        stale_cv_ids = previously_matched_cv_ids - newly_qualified_cv_ids
        if stale_cv_ids:
            Match.objects.filter(job=job, cv_id__in=stale_cv_ids).delete()
            for stale_cv_id in stale_cv_ids:
                publish_match_invalidated(stale_cv_id, job.job_id, reason="job_updated")
            logger.info(
                "matches_invalidated",
                extra={"job_id": str(job_id), "cv_ids": list(stale_cv_ids)}
                
            )