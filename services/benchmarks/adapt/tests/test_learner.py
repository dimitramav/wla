"""BKT learner unit tests. All four checks from 09-RESEARCH.md §Validation Architecture C1."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from benchmarks.adapt.learner import (
    DEFAULT_BKT, Learner,
    evidence_update, transit_update, bkt_step, response_probability,
)


def test_evidence_update_correct():
    result = evidence_update(0.5, True, p_S=0.1, p_G=0.2)
    assert abs(result - (0.45 / 0.55)) < 1e-9


def test_evidence_update_incorrect():
    result = evidence_update(0.5, False, p_S=0.1, p_G=0.2)
    assert abs(result - (0.05 / 0.45)) < 1e-9


def test_transit_update_monotone():
    for p_post in [0.0, 0.1, 0.5, 0.9, 1.0]:
        for p_T in [0.0, 0.1, 0.3]:
            assert transit_update(p_post, p_T) >= p_post - 1e-12


def test_response_simulator_frequency():
    p_correct = response_probability(0.9, {"p_S": 0.1, "p_G": 0.2})
    assert abs(p_correct - 0.83) < 1e-9


def test_prior_seeding_weak_fraction():
    kws = [f"kw_{i}" for i in range(100)]
    learner = Learner(keywords=kws, seed=42)
    fraction_weak = len(learner.initially_weak) / 100
    assert abs(fraction_weak - 0.30) < 0.05
    for kw in learner.initially_weak:
        assert 0.1 <= learner.mastery[kw] <= 0.3
    for kw in learner.initially_strong:
        assert 0.6 <= learner.mastery[kw] <= 0.8


def test_bkt_step_combines_evidence_and_transit():
    p_L = 0.3
    params = {"p_S": 0.08, "p_G": 0.22, "p_T": 0.15}
    new_p = bkt_step(p_L, True, params)
    expected_evidence = 0.3 * 0.92 / (0.3 * 0.92 + 0.7 * 0.22)
    expected_transit = expected_evidence + (1.0 - expected_evidence) * 0.15
    assert abs(new_p - expected_transit) < 1e-9


def test_dynamic_weak_set_recomputes():
    learner = Learner(keywords=["a", "b", "c"], seed=1)
    learner.mastery = {"a": 0.9, "b": 0.2, "c": 0.6}
    assert learner.dynamic_weak_set() == ["b"]
    learner.mastery["a"] = 0.1
    assert learner.dynamic_weak_set() == ["a", "b"]


def test_is_mastered_threshold():
    learner = Learner(keywords=["a", "b"], seed=1)
    learner.mastery = {"a": 0.8, "b": 0.79}
    assert not learner.is_mastered()
    learner.mastery["b"] = 0.8
    assert learner.is_mastered()
