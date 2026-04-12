"""Plot smoke + reproducibility tests."""
import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from benchmarks.adapt.plots import render_learning_curve

ADAPT_CSV_FIELDS = [
    "timestamp", "ratio", "learner_seed", "quiz_index",
    "mean_mastery", "weak_kw_exposure_count", "strong_kw_drift",
    "coverage_entropy", "weak_set_size", "K", "level", "quizzes_to_mastery",
]


def _write_toy_csv(path: Path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("# phase9_seed=0 ratios=[0.0, 0.65, 1.0] n_learners=3 n_quizzes=4 bootstrap_seed=1 ts=toy\n")
        w = csv.DictWriter(f, fieldnames=ADAPT_CSV_FIELDS)
        w.writeheader()
        seed_base = 1
        for ratio in [0.0, 0.65, 1.0]:
            for learner in range(3):
                for q in range(1, 5):
                    w.writerow({
                        "timestamp": "toy",
                        "ratio": ratio,
                        "learner_seed": seed_base + learner,
                        "quiz_index": q,
                        "mean_mastery": 0.3 + 0.15 * q + 0.05 * ratio,
                        "weak_kw_exposure_count": q,
                        "strong_kw_drift": 0.0,
                        "coverage_entropy": 0.5,
                        "weak_set_size": 2,
                        "K": 5,
                        "level": "1",
                        "quizzes_to_mastery": 5,
                    })


def test_plot_smoke_produces_png(tmp_path):
    csv_path = tmp_path / "adapt_toy.csv"
    _write_toy_csv(csv_path)
    out = tmp_path / "adapt_toy.png"
    render_learning_curve(csv_path=csv_path, output_path=out, ratios=[0.0, 0.65, 1.0])
    assert out.exists()
    assert out.stat().st_size > 5_000, f"PNG suspiciously small: {out.stat().st_size} bytes"


def test_plot_reproducibility_same_seed(tmp_path):
    csv_path = tmp_path / "adapt_toy.csv"
    _write_toy_csv(csv_path)
    out_a = tmp_path / "a.png"
    out_b = tmp_path / "b.png"
    render_learning_curve(csv_path=csv_path, output_path=out_a, ratios=[0.0, 0.65, 1.0], bootstrap_seed=42)
    render_learning_curve(csv_path=csv_path, output_path=out_b, ratios=[0.0, 0.65, 1.0], bootstrap_seed=42)
    assert out_a.read_bytes() == out_b.read_bytes(), "same-seed plot renders differ byte-for-byte"
