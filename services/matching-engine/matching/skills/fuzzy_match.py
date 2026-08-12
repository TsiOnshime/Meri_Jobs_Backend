"""difflib-based fallback for typos / near-miss skill names."""
from difflib import SequenceMatcher
from matching.models import Skill


FUZZY_MATCH_THRESHOLD = 0.90

_canonical_names_cache: list[tuple[str, str]] | None = None

def _load_canonical_names() -> list[tuple[str, str]]:
    global _canonical_names_cache
    if _canonical_names_cache is None:
        _canonical_names_cache = list(
            Skill.objects.values_list("name", "id")
        )
    
    return _canonical_names_cache

def fuzzy_resolve(normailzed_skill: str) -> str | None:
    best_id = None
    best_score = 0.0
    
    for name, skill_id in _load_canonical_names():
        score = SequenceMatcher(None, normailzed_skill, name).ratio()
        if score > best_score:
            best_score = score
            best_id = skill_id
        
        if best_score >= FUZZY_MATCH_THRESHOLD:
            return str(best_id)
    return None