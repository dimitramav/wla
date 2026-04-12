"""CSV schema + header-comment + determinism tests for Phase 9 runner."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

SERVICES_DIR = Path(__file__).resolve().parents[3]
RESULTS_DIR = SERVICES_DIR / "benchmarks" / "results"

ADAPT_CSV_FIELDS = [
    "timestamp", "ratio", "learner_seed", "quiz_index",
    "mean_mastery", "weak_kw_exposure_count", "strong_kw_drift",
    "coverage_entropy", "weak_set_size", "K", "level", "quizzes_to_mastery",
]


def _run_tiny():
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    subprocess.run(
        [sys.executable, "-m", "benchmarks.adapt_benchmark", "--tiny", "--no-plot"],
        cwd=SERVICES_DIR, env=env, check=True,
    )
    csvs = sorted(RESULTS_DIR.glob("adapt_*.csv"), key=lambda p: p.stat().st_mtime)
    return csvs[-1]


def test_csv_schema_conformance():
    path = _run_tiny()
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    header = lines[0].strip().split(",")
    assert set(header) == set(ADAPT_CSV_FIELDS)
    data_rows = lines[1:]
    assert len(data_rows) == 36, f"expected 36 rows, got {len(data_rows)}"


def test_csv_header_comment_line():
    path = _run_tiny()
    with open(path, "r", encoding="utf-8") as f:
        first = f.readline()
    assert first.startswith("# phase9_seed=")
    for token in ["ratios=", "n_learners=", "n_quizzes=", "bootstrap_seed=", "ts=", "pythonhashseed="]:
        assert token in first, f"missing token {token!r} in header comment"


def test_csv_determinism():
    a = _run_tiny().read_text(encoding="utf-8")
    b = _run_tiny().read_text(encoding="utf-8")

    def _strip_nondeterministic(text):
        out = []
        for ln in text.splitlines():
            if ln.startswith("#"):
                continue
            if ln.startswith("timestamp,"):
                out.append(ln)
                continue
            parts = ln.split(",")
            parts[0] = "IGNORED"  # strip timestamp column value
            out.append(",".join(parts))
        return "\n".join(out)

    assert _strip_nondeterministic(a) == _strip_nondeterministic(b), (
        "Two --tiny runs under the same seed differ — determinism regression"
    )
