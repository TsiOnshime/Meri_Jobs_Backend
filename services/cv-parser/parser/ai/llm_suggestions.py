"""
Optional, decoupled LLM layer (see system design doc: 'LLM (optional,
decoupled)' under cv-parser's Patterns & Tech).

Generates richer suggestions and judges "clarity" using an LLM, since
judging vague vs. concrete writing is fundamentally a language task an
LLM is better suited for than the regex-based rules.

Falls back cleanly to the rule-based suggestions.py / scoring.py if the
LLM is disabled, misconfigured, times out, or returns something we can't
parse -- FR-C4/FR-C5 must still work with zero AI involved, since this
is explicitly meant to be optional and decoupled, not a hard dependency.
"""
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are reviewing a candidate's CV. Based on the raw text below, return ONLY a JSON object (no markdown, no commentary) with this exact shape:

{{
  "suggestions": [
    {{"type": "missing_keyword" | "weak_bullet" | "unquantified", "field_reference": "string", "suggestion_text": "string"}}
  ],
  "clarity_score": <integer 0-100, how clear/quantified/results-oriented the writing is>,
  "experience_years": <integer, total combined years of professional experience across all roles. Use 0 if none>,
  "role_category": <string, categorize the candidate's primary profession in 1-3 words (e.g., 'Software Engineering', 'Data Science', 'Marketing')>
}}

Give at most 8 suggestions, focused on the most impactful improvements.

CV TEXT:
---
{cv_text}
---
"""


def get_llm_suggestions_and_clarity(raw_text: str):
    """
    Returns (suggestions: list[dict], clarity_score: int, experience_years: int, role_category: str), 
    or None if the LLM path isn't usable right now -- caller must fall back to rules.
    """
    if not settings.LLM_ENABLED or not settings.GROQ_API_KEY:
        return None

    try:
        from openai import OpenAI  # Groq's API is OpenAI-compatible

        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise CV-review assistant. "
                                               "Always respond with valid JSON only."},
                {"role": "user", "content": PROMPT_TEMPLATE.format(cv_text=raw_text[:6000])},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)

        clarity_score = int(parsed.get("clarity_score", 50))
        clarity_score = max(0, min(100, clarity_score))  # don't trust the model blindly

        # Extract the two new AI-calculated fields
        experience_years = int(parsed.get("experience_years", 0))
        role_category = str(parsed.get("role_category", "unspecified"))

        raw_suggestions = parsed.get("suggestions", [])
        clean_suggestions = []
        for s in raw_suggestions:
            if not (isinstance(s, dict) and s.get("suggestion_text")
                    and s.get("type") in ("missing_keyword", "weak_bullet", "unquantified")):
                continue
            s["field_reference"] = str(s.get("field_reference", ""))[:250]
            clean_suggestions.append(s)
        return clean_suggestions, clarity_score, experience_years, role_category

    except Exception as exc:
        logger.warning("LLM suggestions failed: %s", exc, exc_info=True)
        return None