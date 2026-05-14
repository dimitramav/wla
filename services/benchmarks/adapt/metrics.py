"""Per-run metrics for Phase 9 adaptive scheduler validation.

Formulas copied verbatim from 09-RESEARCH.md Q7. See the Validation Architecture
section for hand-computed unit-test expectations.
"""
import math
from typing import Dict, List, Set
from .learner import MASTERY_THRESHOLD


def quizzes_to_mastery(history: List[Dict[str, float]], max_quizzes: int) -> int:
    """First quiz index (1-based) at which every keyword reached mastery.
    Returns max_quizzes + 1 as a numeric sentinel if never reached."""
    for q, state in enumerate(history, start=1):
        if all(v >= MASTERY_THRESHOLD for v in state.values()):
            return q
    return max_quizzes + 1


def weak_kw_exposure_count(targets_per_quiz: List[List[str]], initially_weak: Set[str]) -> int:
    """Total targeted appearances of initially-weak keywords across the run."""
    return sum(
        1 for quiz in targets_per_quiz for kw in quiz if kw in initially_weak
    )


def strong_kw_drift(initial: Dict[str, float], final: Dict[str, float], initially_strong: Set[str]) -> float:
    """Signed mean delta on the initially-strong set. Negative = catastrophic forgetting."""
    if not initially_strong:
        return 0.0
    return sum(final[k] - initial[k] for k in initially_strong) / len(initially_strong)


def coverage_entropy(targets_per_quiz: List[List[str]], all_keywords: List[str]) -> float:
    """Normalized Shannon entropy of the per-keyword exposure distribution in [0, 1].

    1.0 = perfectly uniform coverage across K keywords.
    0.0 = all exposures concentrated on a single keyword.
    """
    K = len(all_keywords)
    counts = {kw: 0 for kw in all_keywords}
    total = 0
    for quiz in targets_per_quiz:
        for kw in quiz:
            if kw in counts:
                counts[kw] += 1
                total += 1
    if total == 0 or K <= 1:
        return 0.0
    probs = [c / total for c in counts.values() if c > 0]
    H = -sum(p * math.log(p) for p in probs)
    return H / math.log(K)
