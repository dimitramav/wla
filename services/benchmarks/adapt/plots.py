"""Learning-curve figure for Phase 9 — mastery over time by ratio with 95% bootstrap CI.

D-17: matplotlib, 95% bootstrap CI per ratio.
Q8: Agg backend (headless), figsize (10,6), dpi 150, 1000 bootstrap resamples.
"""
from pathlib import Path
from typing import Iterable
import csv

import matplotlib
matplotlib.use("Agg")  # MUST be before pyplot import (Q12 risk)
import matplotlib.pyplot as plt
import numpy as np


FIG_SIZE = (10, 6)
FIG_DPI = 150
BOOTSTRAP_RESAMPLES = 1000
CI_LOW = 2.5
CI_HIGH = 97.5


def _load_rows(csv_path: Path):
    """Load rows from the adapt CSV, skipping comment lines starting with '#'."""
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    reader = csv.DictReader(lines)
    return list(reader)


def _mastery_matrix(rows, ratio):
    """Return a (n_learners, n_quizzes) matrix of mean_mastery values for one ratio."""
    by_learner = {}
    for r in rows:
        if float(r["ratio"]) != float(ratio):
            continue
        ls = r["learner_seed"]
        by_learner.setdefault(ls, []).append((int(r["quiz_index"]), float(r["mean_mastery"])))
    if not by_learner:
        return np.zeros((0, 0))
    for ls in by_learner:
        by_learner[ls].sort(key=lambda x: x[0])
    seeds = sorted(by_learner.keys())
    rows_out = [[m for _, m in by_learner[s]] for s in seeds]
    return np.array(rows_out, dtype=float)


def _bootstrap_mean_ci(matrix: np.ndarray, resamples: int, seed: int):
    """Per-column (per-quiz) mean with 95% bootstrap CI across rows (learners)."""
    n, cols = matrix.shape
    if n == 0 or cols == 0:
        return np.zeros(0), np.zeros(0), np.zeros(0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(resamples, n))
    sampled_means = matrix[idx].mean(axis=1)  # (resamples, cols)
    lo = np.percentile(sampled_means, CI_LOW, axis=0)
    hi = np.percentile(sampled_means, CI_HIGH, axis=0)
    mean = matrix.mean(axis=0)
    return mean, lo, hi


def render_learning_curve(
    *,
    csv_path: Path,
    output_path: Path,
    ratios: Iterable[float],
    bootstrap_seed: int = 67890,
) -> Path:
    """Render a per-ratio mean-mastery line chart with bootstrap 95% CI bands."""
    rows = _load_rows(Path(csv_path))
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)

    for ratio in ratios:
        matrix = _mastery_matrix(rows, ratio)
        if matrix.size == 0:
            continue
        mean, lo, hi = _bootstrap_mean_ci(matrix, BOOTSTRAP_RESAMPLES, bootstrap_seed)
        xs = np.arange(1, matrix.shape[1] + 1)
        label = f"ratio={ratio}" + (" (default)" if ratio == 0.65 else "")
        line, = ax.plot(xs, mean, label=label)
        ax.fill_between(xs, lo, hi, alpha=0.2, color=line.get_color())

    ax.set_xlabel("Quiz index")
    ax.set_ylabel("Mean mastery across learner cohort")
    ax.set_title("Phase 9 — Learning curves by weak-focus ratio (95% bootstrap CI)")
    ax.set_ylim(0.0, 1.05)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=FIG_DPI)
    plt.close(fig)
    return Path(output_path)
