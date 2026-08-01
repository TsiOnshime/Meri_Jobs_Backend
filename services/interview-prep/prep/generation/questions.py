"""LLM prompt/response handling for mock question generation, isolated here."""
from .client import generate_json

QUESTION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
            "question_type": {
                "type": "string",
                "enum": ["open_ended", "multiple_choice"],
            },
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Exactly 4 items for multiple_choice questions. "
                    "Empty array for open_ended."
                ),
            },
            "correct_option": {
                "type": "integer",
                "description": (
                    "Index into options for the correct answer. "
                    "-1 for open_ended questions."
                ),
            },
        },
        "required": [
            "text",
            "difficulty",
            "question_type",
            "options",
            "correct_option",
        ],
    },
}

# Static per question_type, not per-question from the model -- keeps the
# time budget predictable regardless of what the LLM returns.
TIME_LIMITS = {
    "multiple_choice": 60,
    "open_ended": 300,
}


def generate_questions(job_title: str, focus_area: str, count: int = 10) -> list[dict]:
    """Generate `count` mock interview questions, all open_ended.

    Returns a list of dicts shaped for direct use when creating Question
    rows: {text, difficulty, question_type, options, correct_option,
    time_limit}. round_number is assigned by the caller, not here.
    """
    prompt = (
        f"Generate exactly {count} mock technical interview questions for a "
        f"candidate interviewing for the role of "
        f"'{job_title or 'Software Engineer'}', focused on "
        f"'{focus_area or 'general software engineering'}'.\n"
        f"Mix difficulty levels (easy/medium/hard) across the set.\n"
        f"Every question must be question_type open_ended (the candidate "
        f"explains something in free text). Do not generate multiple_choice "
        f"questions.\n"
        f"For every question, options must be an empty array and "
        f"correct_option must be -1."
    )

    raw_questions = generate_json(prompt, QUESTION_SCHEMA)

    # Defensive normalization -- never fully trust a free-tier model to hit
    # `count` exactly or to actually respect the "open_ended only"
    # instruction. Every question is forced to open_ended here regardless
    # of what question_type the model returned, so a stray multiple_choice
    # response can never leak through to the frontend.
    normalized = []
    for q in raw_questions[:count]:
        normalized.append(
            {
                "text": q["text"],
                "difficulty": q.get("difficulty", "medium"),
                "question_type": "open_ended",
                "options": None,
                "correct_option": None,
                "time_limit": TIME_LIMITS["open_ended"],
            }
        )

    return normalized