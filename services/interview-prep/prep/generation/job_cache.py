"""Redis-backed cache for pre-generated questions, keyed by job.

Written to by the match_found consumer (best-effort pre-generation, see
prep/consumers/match_found_consumer.py) and read by create_session so a
candidate who starts a mock interview for a job that was already
pre-generated gets an instant response instead of waiting on a fresh
Gemini call.

Uses the `redis` package directly rather than Django's cache framework --
there's no django-redis in requirements.txt, and this is simple enough
(get/set/delete of one JSON blob) not to need it. Deliberately on
REDIS db=1, separate from Celery's broker/result-backend db=0, so a
`FLUSHDB` against one doesn't take out the other.
"""
import json

import redis
from django.conf import settings

_redis_client = None

# Long enough to cover the gap between a match being found and the
# candidate actually starting a mock interview for it; short enough that
# a stale question set doesn't sit around forever if the job listing
# changes before anyone starts a session against it.
CACHE_TTL_SECONDS = 60 * 60 * 24 * 7  # 1 week


def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=1,
            decode_responses=True,
        )
    return _redis_client


def _cache_key(job_id, focus_area):
    # focus_area is part of the key because generate_questions() prompts
    # differently per focus_area -- a job with no focus_area set shouldn't
    # collide with (or serve stale results to) a session that specifies
    # e.g. "backend" vs "frontend" for the same job_id.
    return f"job_questions:{job_id}:{focus_area or 'general'}"


def set_cached_questions(job_id, focus_area, questions: list[dict]) -> None:
    _get_redis().setex(
        _cache_key(job_id, focus_area), CACHE_TTL_SECONDS, json.dumps(questions)
    )


def pop_cached_questions(job_id, focus_area) -> list[dict] | None:
    """Read and delete the cached question set for one job, if present.

    Deletes on read rather than just GET: a pre-generated set is a
    one-shot head start for whichever session picks it up first, not a
    shared bank later sessions for the same job would otherwise reuse
    verbatim (which would mean every candidate for that job seeing
    identical questions).
    """
    client = _get_redis()
    key = _cache_key(job_id, focus_area)
    raw = client.get(key)
    if raw is None:
        return None
    client.delete(key)
    return json.loads(raw)