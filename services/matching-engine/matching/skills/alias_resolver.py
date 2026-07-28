"""Redis-backed alias -> canonical skill id lookup."""
import redis
from django.conf import settings

__redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
)

def resolve_alias(normalized_skill: str) -> str | None:
    key = f"skill_alias:{normalized_skill}"
    return __redis_client.get(key)

def refresh_alias_cache():
    from matching.models import SkillAlias
    
    pipe = __redis_client.pipeline()
    
    for alias in SkillAlias.objects.select_related("skill").all():
        pipe.set(f"skill_alias:{alias.alias_name}", str(alias.skill_id))
    pipe.execute()