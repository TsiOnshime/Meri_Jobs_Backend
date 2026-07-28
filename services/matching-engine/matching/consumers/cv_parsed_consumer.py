"""Consumes cv.parsed: resolves skills, filters jobs, scores, reconciles if edit."""
import logging 
from matching.models import CV, Job, Match
from matching.skills.resolve import resolve_skills
from matching.scoring.gate import passes_gate
from matching.scoring.weighted_score import compute_score
from matching.publishers.match_found import publish_match_found
from matching.publishers.match_invalidated import publish_match_invalidated

logger = logging.getLogger(__name__)

def handle_cv_parsed(event: dict) -> None:
    cv_id = event["cv_id"]
    
    is_edit = CV.objects.filter(cv_id=cv_id).exists()
    
    previously_matched_job_ids = set()
    if is_edit:
        previously_matched_job_ids = set(
            Match.objects.filter(cv=cv_id).values_list("job_id", flat=True)
        )
    
    resolved_skill_ids = resolve_skills(event["raw_skills"])
    
    cv, _ = CV.objects.update_or_create(
        cv_id=cv_id,
        defaults={
            "skill_ids": resolved_skill_ids,
            "experience_years": event["experience_years"],
            "seniority": event["seniority"],
            "role_category": event["role_category"]
        },
    )
    candidate_jobs = Job.objects.filter(role_category=cv.role_category)
    
    newly_qualified_job_ids = set()
    
    for job in candidate_jobs:
        gate_result = passes_gate(cv, job)
        if not gate_result.passed:
            continue
        overall_score, breakdown = compute_score(cv, job, gate_result)
        
        Match.objects.update_or_create(
            cv=cv,
            job=job,
            defaults={"overall_score": overall_score, "breakdown": breakdown}
        )
        
        newly_qualified_job_ids.add(job.job_id)
        
        publish_match_found(cv, job, overall_score, breakdown)
    if is_edit:
        stale_job_ids = previously_matched_job_ids - newly_qualified_job_ids
        if stale_job_ids:
            Match.objects.filter(cv=cv, job_id__in=stale_job_ids).delete()
            for stale_job_id in stale_job_ids:
                publish_match_invalidated(cv.cv_id, stale_job_id, reason="cv_updated")
            logger.info(
                "matches_invalidated",
                extra={"cv_id": str(cv_id), "job_ids": list(stale_job_ids)}
            )