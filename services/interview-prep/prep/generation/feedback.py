"""LLM prompt/response handling for answer feedback.

Only used for open_ended answers. multiple_choice answers are graded
synchronously and deterministically (selected_option == correct_option),
no LLM call needed -- see prep/scoring.py.
"""
from .client import generate_json

FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "number",
            "description": "0-10, one decimal place",
        },
        "strengths": {"type": "array", "items": {"type": "string"}},
        "improvements": {"type": "array", "items": {"type": "string"}},
        "suggested_answer": {"type": "string"},
    },
    "required": ["score", "strengths", "improvements", "suggested_answer"],
}


def generate_feedback(question_text: str, answer_text: str) -> dict:
    """Score a candidate's open-ended answer and return structured feedback.

    Returns {score, strengths, improvements, suggested_answer}, matching
    the shape prep/tasks.py writes straight onto the Answer row.
    """
    prompt = (
        "You are a technical interviewer giving feedback on a practice "
        "answer.\n\n"
        f"Question: {question_text}\n\n"
        f"Candidate's answer: {answer_text}\n\n"
        "Score the answer from 0-10 (one decimal place). List 1-3 specific "
        "strengths and 1-3 specific improvements. Write a concise model "
        "answer a strong candidate would give."
    )

    result = generate_json(prompt, FEEDBACK_SCHEMA, temperature=0.3)

    return {
        "score": float(result["score"]),
        "strengths": result["strengths"],
        "improvements": result["improvements"],
        "suggested_answer": result["suggested_answer"],
    }