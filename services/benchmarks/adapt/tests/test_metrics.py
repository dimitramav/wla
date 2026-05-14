"""Metric unit tests. Hand-computed inputs from 09-RESEARCH.md §Validation Architecture C3."""
import sys
from pathlib import Path
import math

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from benchmarks.adapt.metrics import (
    quizzes_to_mastery, weak_kw_exposure_count,
    strong_kw_drift, coverage_entropy,
)


def test_quizzes_to_mastery_reached_at_three():
    history = [
        {"a": 0.5, "b": 0.5},
        {"a": 0.7, "b": 0.7},
        {"a": 0.85, "b": 0.82},
        {"a": 0.9,  "b": 0.88},
    ]
    assert quizzes_to_mastery(history, max_quizzes=25) == 3


def test_quizzes_to_mastery_never_reached_returns_sentinel():
    history = [{"a": 0.3}, {"a": 0.4}, {"a": 0.5}]
    assert quizzes_to_mastery(history, max_quizzes=25) == 26


def test_weak_kw_exposure_count_hand_computed():
    targets = [["w1", "w1"], ["s1"], ["w1", "w2"]]
    initially_weak = {"w1", "w2"}
    assert weak_kw_exposure_count(targets, initially_weak) == 4


def test_strong_kw_drift_signed_mean_delta():
    initial = {"a": 0.7, "b": 0.6, "c": 0.75}
    final   = {"a": 0.8, "b": 0.5, "c": 0.75}
    initially_strong = {"a", "b", "c"}
    assert abs(strong_kw_drift(initial, final, initially_strong)) < 1e-9


def test_coverage_entropy_uniform_maxes_at_one():
    targets = [["a", "b", "c", "d", "e"]]
    all_kws = ["a", "b", "c", "d", "e"]
    assert abs(coverage_entropy(targets, all_kws) - 1.0) < 1e-9


def test_coverage_entropy_single_keyword_is_zero():
    targets = [["a", "a", "a"]]
    all_kws = ["a", "b", "c"]
    assert coverage_entropy(targets, all_kws) == 0.0


def test_coverage_entropy_middle_case_hand_computed():
    targets = [["a", "a"], ["b"]]
    all_kws = ["a", "b", "c"]
    expected_H = -(2/3 * math.log(2/3) + 1/3 * math.log(1/3))
    expected = expected_H / math.log(3)
    assert abs(coverage_entropy(targets, all_kws) - expected) < 1e-9


def test_coverage_entropy_empty_returns_zero():
    assert coverage_entropy([], ["a", "b"]) == 0.0
