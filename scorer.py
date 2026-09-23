"""
Scorer for evaluating pipeline answers.

Provides `judge(...)` which run_eval.py imports automatically.
"""

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


def judge(question: str, expects: str, answer: str, results=None, threshold: float = 70.0) -> bool:
    """
    Judges whether the answer satisfies the expectation using fuzzy matching.

    - Fast path: exact substring match (case-insensitive).
    - Fuzzy path: uses rapidfuzz to handle minor phrasing differences, typos,
      and word ordering variations.
    """
    if not expects or not answer:
        return False

    exp = expects.lower().strip()
    ans = answer.lower().strip()

    # 1. Exact substring check (same as simple original logic)
    if exp in ans:
        return True

    # 2. Fuzzy match with rapidfuzz if installed
    if fuzz is not None:
        # partial_ratio checks for fuzzy substring alignment;
        # token_set_ratio checks for token overlap regardless of word order.
        score = max(fuzz.partial_ratio(exp, ans), fuzz.token_set_ratio(exp, ans))
        return score >= threshold

    return False