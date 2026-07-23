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
    """Generate `count` mock interview questions, mixing question types.

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
        f"Mix question_type across the set: roughly half open_ended "
        f"(the candidate explains something in free text) and half "
        f"multiple_choice (exactly 4 options, exactly one correct).\n"
        f"For open_ended questions, options must be an empty array and "
        f"correct_option must be -1."
    )

    raw_questions = generate_json(prompt, QUESTION_SCHEMA)

    # Defensive normalization -- never fully trust a free-tier model to hit
    # `count` exactly or to respect the "empty options for open_ended" rule.
    normalized = []
    for q in raw_questions[:count]:
        q_type = q.get("question_type")
        if q_type not in ("open_ended", "multiple_choice"):
            q_type = "open_ended"

        if q_type == "multiple_choice":
            options = q.get("options") or []
            correct_option = q.get("correct_option")
            # If the model gave us something unusable for a multiple-choice
            # question, fall back to open_ended rather than shipping a
            # broken question to the frontend.
            if len(options) < 2 or not isinstance(correct_option, int) or not (
                0 <= correct_option < len(options)
            ):
                q_type = "open_ended"
                options = None
                correct_option = None
        else:
            options = None
            correct_option = None

        normalized.append(
            {
                "text": q["text"],
                "difficulty": q.get("difficulty", "medium"),
                "question_type": q_type,
                "options": options,
                "correct_option": correct_option,
                "time_limit": TIME_LIMITS[q_type],
            }
        )

    return normalized