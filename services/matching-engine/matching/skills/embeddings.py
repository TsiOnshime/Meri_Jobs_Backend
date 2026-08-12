import numpy as np
from sentence_transformers import SentenceTransformer
from matching.models import Skill

EMBEDDING_MATCH_THRESHOLD = 0.4
MODEL_NAME = "all-MiniLM-L6-v2"

_model = None
_canonical_embeddings_cache = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def _load_canonical_embeddings():
    global _canonical_embeddings_cache
    if _canonical_embeddings_cache is None:
        skills = list(Skill.objects.values_list("id", "name"))

        skill_ids = [str(skill_id) for skill_id, _ in skills]
        names = [name for _, name in skills]
        
        model = _get_model()
        
        embeddings = model.encode(names, normalize_embeddings=True)
        
        _canonical_embeddings_cache = (skill_ids, embeddings)
        
    return _canonical_embeddings_cache


def embedding_resolve(normalized_skill: str) -> str | None:

    skill_ids, canonical_embeddings = _load_canonical_embeddings()

    if not skill_ids:
        return None

    model = _get_model()
    
    query_embedding = model.encode([normalized_skill], normalize_embeddings=True)[0]

    similarities = canonical_embeddings @ query_embedding
    best_index = int(np.argmax(similarities))
    best_score = float(similarities[best_index])

    if best_score >= EMBEDDING_MATCH_THRESHOLD:
        return skill_ids[best_index]
    return None