"""Required-skills / min-experience / location pass-fail check."""
from dataclasses import dataclass, field
from matching.models import CV, Job

REQUIRED_SKILL_COVERAGE = 1.0

@dataclass
class GateResult:
    passed: bool
    matched_skill_ids: set[str] = field(default_factory=set)
    missing_skill_ids: set[str] = field(default_factory=set)
    
def passes_gate(cv:CV, job:Job) -> GateResult:
    cv_skill_ids = set(cv.skill_ids)
    job_skill_ids = set(job.skill_ids)
    
    matched = cv_skill_ids & job_skill_ids
    missing = job_skill_ids - cv_skill_ids
    
    required_count = len(job_skill_ids)
    coverage = len(matched) / required_count if required_count > 0 else 1.0
    
    skills_pass = coverage >= REQUIRED_SKILL_COVERAGE
    experience_pass = cv.experience_years >= job.min_experience
    
    return GateResult(
        passed=skills_pass and experience_pass, 
        matched_skill_ids=matched,
        missing_skill_ids=missing,
    )