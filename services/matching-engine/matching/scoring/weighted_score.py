"""0.5 skill + 0.3 experience + 0.2 seniority formula."""
from matching.models import Skill, CV, Job
from matching.scoring.gate import GateResult

SKILL_WEIGHT = 0.5
EXPERIENCE_WEIGHT = 0.3
SENIORITY_WEIGHT = 0.2

SENIORITY_ORDER = ["junior", "mid", "senior", "lead"]

SENIORITY_SCORE_BY_DISTANCE = {
    0: 100, #exact match
    1: 75,  #one level away
    2: 50,  #two levels away
    3: 25,  #three levels away
}

def _skill_names(skill_ids: set[str]) -> list[str]:
    if not skill_ids:
        return []
    return list(
        Skill.objects.filter(id__in=skill_ids).values_list("name", flat=True)
    )
    
def _seniority_score(candidate_level: str, required_level:str) -> int:
    candidate_index = SENIORITY_ORDER.index(candidate_level)
    required_index = SENIORITY_ORDER.index(required_level)
    
    distance = abs(candidate_index - required_index)
    return SENIORITY_SCORE_BY_DISTANCE.get(distance, 0)

def compute_score(cv: CV, job: Job, gate_result: GateResult) -> tuple[int, dict]:
    required_count = len(job.skill_ids)
    matched_count = len(gate_result.matched_skill_ids)
    skill_score = (matched_count / required_count * 100) if required_count > 0 else 100
    
    experience_score = min(cv.experience_years / job.min_experience, 1) * 100 if job.min_experience > 0 else 100
    
    seniority_score = _seniority_score(cv.seniority, job.seniority_level)
    
    overall_score = round(
        SKILL_WEIGHT * skill_score + EXPERIENCE_WEIGHT * experience_score + SENIORITY_WEIGHT * seniority_score
    )
    
    breakdown = {
        "skills": {
            "matched": _skill_names(gate_result.matched_skill_ids),
            "missing": _skill_names(gate_result.missing_skill_ids), 
            "matched_count": matched_count,
            "required_count": required_count,
            "score": round(skill_score),
        },
        "experience": {
            "required_years": job.min_experience,
            "candidate_years": cv.experience_years,
            "score": round(experience_score)
        },
        "seniority": {
            "candidate": cv.seniority,
            "required": job.seniority_level,
            "score": seniority_score,
        },
            
    }
    
    return overall_score, breakdown