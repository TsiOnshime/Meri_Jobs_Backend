"""Confidence scoring and CV scoring. Rules-based and explainable on purpose."""

REQUIRED_FIELDS_WEIGHTS = {
    "name": 0.25,
    "email": 0.25,
    "experience": 0.30,
    "skills": 0.20,
}

VAGUE_VERBS = ["improved", "helped", "responsible for", "worked on", "assisted with"]


def _field_confidence(field_name, value):
    if value in (None, "", [], {}):
        return 0.0
    if field_name == "email":
        return 1.0 if "@" in str(value) and "." in str(value) else 0.2
    if field_name in ("experience", "education", "skills", "certifications"):
        return 1.0 if len(value) > 0 else 0.0
    return 1.0 if value else 0.0


def compute_confidence(fields: dict) -> tuple[float, list[str]]:
    """Returns (overall_confidence 0-1, flagged_sections)."""
    flagged, weighted_sum, total_weight = [], 0.0, 0.0
    for field, weight in REQUIRED_FIELDS_WEIGHTS.items():
        conf = _field_confidence(field, fields.get(field))
        weighted_sum += conf * weight
        total_weight += weight
        if conf < 0.5:
            flagged.append(field)
    return round(weighted_sum / total_weight, 2) if total_weight else 0.0, flagged


def compute_cv_score(fields: dict, target_keywords: list[str] | None = None,
                      clarity_override: int | None = None) -> dict:
    """CV score explicitly split into completeness / keyword_relevance / clarity.

    clarity_override lets the caller plug in an LLM-judged clarity score
    (see parser/ai/llm_suggestions.py) instead of the regex-based one below --
    completeness and keyword_relevance stay rule-based either way, since
    those are about presence/overlap, not writing quality."""
    target_keywords = target_keywords or []

    expected = ["name", "email", "phone", "education", "experience", "skills"]
    completeness = round((sum(1 for s in expected if fields.get(s)) / len(expected)) * 100)

    skills = {s.lower() for s in fields.get("skills", [])}
    if target_keywords:
        matched = skills.intersection({k.lower() for k in target_keywords})
        keyword_relevance = round((len(matched) / len(target_keywords)) * 100)
    else:
        keyword_relevance = min(100, len(skills) * 10)

    if clarity_override is not None:
        clarity = max(0, min(100, clarity_override))
    else:
        bullets = []
        for job in fields.get("experience", []):
            bullets.extend(job.get("bullets", []) if isinstance(job, dict) else [])
        if bullets:
            vague = sum(
                1 for b in bullets
                if any(v in b.lower() for v in VAGUE_VERBS) and not any(c.isdigit() for c in b)
            )
            clarity = round(100 * (1 - vague / len(bullets)))
        else:
            clarity = 50

    overall = round(completeness * 0.4 + keyword_relevance * 0.3 + clarity * 0.3)
    return {
        "overall": overall,
        "completeness": completeness,
        "keyword_relevance": keyword_relevance,
        "clarity": clarity,
    }