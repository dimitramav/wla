"""BKT-style simulated learner for Phase 9 adaptive scheduler validation.

Four-parameter Bayesian Knowledge Tracing (Corbett & Anderson, 1995).
Parameter bounds: slip <= 0.1, guess <= 0.3 (Baker, Corbett & Aleven, ITS 2008).
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import random
import yaml

DEFAULT_BKT = {
    "p_L0": 0.30,
    "p_T":  0.15,
    "p_S":  0.08,
    "p_G":  0.22,
}

WEAK_THRESHOLD = 0.5
MASTERY_THRESHOLD = 0.8


def evidence_update(p_L: float, observed_correct: bool, p_S: float, p_G: float) -> float:
    """Step 1 of BKT: P(L_n | obs) after an observation."""
    if observed_correct:
        numer = p_L * (1.0 - p_S)
        denom = p_L * (1.0 - p_S) + (1.0 - p_L) * p_G
    else:
        numer = p_L * p_S
        denom = p_L * p_S + (1.0 - p_L) * (1.0 - p_G)
    return numer / denom if denom > 0 else p_L


def transit_update(p_L_post: float, p_T: float) -> float:
    """Step 2 of BKT: P(L_{n+1}) after transit. Monotone non-decreasing in p_L_post."""
    return p_L_post + (1.0 - p_L_post) * p_T


def bkt_step(p_L: float, observed_correct: bool, bkt_params: Dict[str, float]) -> float:
    """One full BKT update: evidence then transit."""
    p_L_post = evidence_update(p_L, observed_correct, bkt_params["p_S"], bkt_params["p_G"])
    return transit_update(p_L_post, bkt_params["p_T"])


def response_probability(p_L: float, bkt_params: Dict[str, float]) -> float:
    """Probability the learner answers correctly for the given mastery."""
    return p_L * (1.0 - bkt_params["p_S"]) + (1.0 - p_L) * bkt_params["p_G"]


@dataclass
class Learner:
    keywords: List[str]
    bkt_params: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_BKT))
    seed: int = 0
    mastery: Dict[str, float] = field(default_factory=dict)
    initially_weak: Set[str] = field(default_factory=set)
    initially_strong: Set[str] = field(default_factory=set)
    initial_mastery: Dict[str, float] = field(default_factory=dict)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self):
        self._rng = random.Random(self.seed)
        self._seed_prior()

    def _seed_prior(self):
        """Seed ~70% keywords as known (p(L) in [0.6, 0.8]) and ~30% as weak ([0.1, 0.3])."""
        kws = sorted(self.keywords)
        n_weak = max(1, round(0.3 * len(kws)))
        weak_pick = set(self._rng.sample(kws, n_weak))
        for kw in kws:
            if kw in weak_pick:
                self.mastery[kw] = self._rng.uniform(0.1, 0.3)
                self.initially_weak.add(kw)
            else:
                self.mastery[kw] = self._rng.uniform(0.6, 0.8)
                self.initially_strong.add(kw)
        self.initial_mastery = dict(self.mastery)

    def dynamic_weak_set(self, threshold: float = WEAK_THRESHOLD) -> List[str]:
        """Recompute the weak keyword set from current mastery. D-04 (dynamic) + D-05 (instant)."""
        return sorted([kw for kw, m in self.mastery.items() if m < threshold])

    def is_mastered(self, threshold: float = MASTERY_THRESHOLD) -> bool:
        return all(m >= threshold for m in self.mastery.values())

    def observe_quiz(self, targeted_keywords: List[str]) -> List[Tuple[str, bool]]:
        """Simulate one quiz. Returns (keyword, correct) pairs for each targeted question."""
        results = []
        for kw in targeted_keywords:
            if kw not in self.mastery:
                continue
            p = response_probability(self.mastery[kw], self.bkt_params)
            correct = self._rng.random() < p
            self.mastery[kw] = bkt_step(self.mastery[kw], correct, self.bkt_params)
            results.append((kw, correct))
        return results


def load_level_keywords(topic: str = "school_anxiety",
                        level: str = "1",
                        content_dir: Optional[Path] = None) -> List[str]:
    """Load keywords for a topic/level from content/<topic>/keywords.yaml."""
    root = content_dir or Path(__file__).resolve().parents[3] / "content"
    fp = root / topic / "keywords.yaml"
    with open(fp, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return list(dict.fromkeys(data[topic][str(level)]))
