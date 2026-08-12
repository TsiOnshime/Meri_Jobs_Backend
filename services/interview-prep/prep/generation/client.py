"""Thin wrapper around the Gemini client, shared by questions.py and feedback.py.

Kept here rather than duplicated in each file so there's exactly one place
that knows how to authenticate and how to ask Gemini for structured JSON.
"""
import json

from decouple import config
from google import genai
from google.genai import types

GEMINI_MODEL = config("GEMINI_MODEL", default="gemini-2.5-flash")

_client = None


def _get_client():
    global _client
    if _client is None:
        # genai.Client() would pick up GEMINI_API_KEY from the environment on
        # its own, but we read it explicitly so a missing key fails loudly
        # and early instead of surfacing as an obscure 401 mid-request.
        api_key = config("GEMINI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client


def generate_json(prompt: str, schema: dict, *, temperature: float = 0.7):
    """Call Gemini and return parsed JSON matching `schema`.

    Raises on any failure (network, empty/malformed response, etc.) --
    callers (Celery tasks, session-creation views) decide how to handle or
    retry that, this stays a dumb pipe.
    """
    response = _get_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        ),
    )
    return json.loads(response.text)