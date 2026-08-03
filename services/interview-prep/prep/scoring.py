"""Deterministic scoring for multiple_choice answers.

Split out from views.py so the thing feedback.py's docstring already
promised ("multiple_choice answers are graded synchronously and
deterministically ... see prep/scoring.py") actually exists, and so the
grading rule lives in exactly one place instead of being inlined in the
view.

No LLM call needed here -- unlike open_ended answers (see
generation/feedback.py, evaluated asynchronously via tasks.py), this is
just an index comparison, so it stays synchronous in the request/response
cycle instead of being queued as a Celery task.
"""


def grade_multiple_choice(question, selected_option: int) -> dict:
    """Grade a multiple_choice answer against `question.correct_option`.

    Returns {score, strengths, improvements} -- the same field names
    tasks.py writes onto an Answer row after an open_ended answer comes
    back from the LLM, minus `suggested_answer`: there's no model answer
    to author for multiple_choice, the options themselves are the answer
    space.
    """
    is_correct = selected_option == question.correct_option
    return {
        "score": 10.0 if is_correct else 0.0,
        "strengths": ["Correct option selected"] if is_correct else [],
        "improvements": (
            []
            if is_correct
            else ["Review this topic -- selected option was incorrect"]
        ),
    }