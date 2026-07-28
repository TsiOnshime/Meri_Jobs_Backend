import logging 
from matching.skills.normalize import normalize
from matching.skills.alias_resolver import resolve_alias
from matching.skills.fuzzy_match import fuzzy_resolve
from matching.skills.embeddings import embedding_resolve
logger = logging.getLogger(__name__)

def resolve_skills(raw_skills: list[str]) -> list[str]:
    resolved_ids: list[str] = []
    
    for raw_skill in raw_skills:
        for normalized_skill in normalize(raw_skill):
            skill_id = resolve_alias(normalized_skill)
            
            if skill_id is None:
                skill_id = fuzzy_resolve(normalized_skill)
            if skill_id is None:
                skill_id = embedding_resolve(normalized_skill)
                
            if skill_id is not None:
                resolved_ids.append(skill_id)
            else:
                logger.info(
                    "unresolved_skill",
                    extra={"raw_skill": raw_skill, "normalized": normalized_skill},
                )
    
    return resolved_ids

