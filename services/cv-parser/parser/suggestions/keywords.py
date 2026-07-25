"""Suggests missing keywords / unquantified achievements."""
"""Suggests missing keywords / unquantified achievements."""
from ..scoring import VAGUE_VERBS

COMMON_TECH_KEYWORDS = [
    "python", "javascript", "typescript", "react", "django", "sql",
    "docker", "kubernetes", "aws", "git", "rest api", "node.js",
]


def generate_suggestions(fields: dict) -> list[dict]:
    suggestions = []
    skills = {s.lower() for s in fields.get("skills", [])}
    raw_text = (fields.get("raw_text", "") or "").lower()

    for keyword in COMMON_TECH_KEYWORDS:
        if keyword not in skills and keyword in raw_text:
            suggestions.append({
                "type": "missing_keyword",
                "field_reference": "skills",
                "suggestion_text": f'"{keyword}" appears in your CV but isn\'t listed as a '
                                    f'skill -- add it so keyword matching picks it up.',
            })

    for job in fields.get("experience", []):
        bullets = job.get("bullets", []) if isinstance(job, dict) else []
        role = job.get("title", "this role") if isinstance(job, dict) else "this role"
        for bullet in bullets:
            lower = bullet.lower()
            has_number = any(c.isdigit() for c in bullet)
            is_vague = any(v in lower for v in VAGUE_VERBS)
            if is_vague and not has_number:
                suggestions.append({
                    "type": "unquantified",
                    "field_reference": f"experience.{role}",
                    "suggestion_text": f'"{bullet}" has no measurable result -- add a '
                                        f'number (e.g. "...by 20%").',
                })
            elif is_vague:
                suggestions.append({
                    "type": "weak_bullet",
                    "field_reference": f"experience.{role}",
                    "suggestion_text": f'"{bullet}" starts with a vague verb -- lead with '
                                        f'the outcome instead.',
                })
    return suggestions
