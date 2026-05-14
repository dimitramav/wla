#!/usr/bin/env python3
"""
Adaptive scheduler validation runner for Watch-Listen-Act Phase 9.

Sweeps weak_focus_ratio across a seeded-learner cohort, simulates quizzes via
the LLM-free plan_only helper, and writes per-snapshot metrics to a timestamped
CSV. Also invokes plots.py to render the learning-curve figure from the CSV.

What this evaluates:
  The empirical validity of the adaptive weak-keyword scheduler: does higher
  weak_focus_ratio accelerate time-to-mastery without regressing strong-keyword
  retention or starving less-weak keywords? This is the core claim tested in
  thesis Chapter 5.

Outputs:
  services/benchmarks/results/adapt_{ts}.csv        — one row per (ratio, learner, quiz)
  services/benchmarks/results/adapt_learning_curve_{ts}.png

Usage:
  cd services && PYTHONHASHSEED=0 python -m benchmarks.adapt_benchmark
  cd services && PYTHONHASHSEED=0 python -m benchmarks.adapt_benchmark --tiny
  cd services && PYTHONHASHSEED=0 python -m benchmarks.adapt_benchmark --smoke
"""

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.config import TOPIC
from benchmarks.io import RESULTS_DIR
from benchmarks.adapt.learner import (
    Learner, DEFAULT_BKT, MASTERY_THRESHOLD, load_level_keywords,
)
from benchmarks.adapt.metrics import (
    quizzes_to_mastery, weak_kw_exposure_count,
    strong_kw_drift, coverage_entropy,
)


# ---------------------------------------------------------------------------
# Experiment parameters (D-07, D-08, D-09, D-10, D-17)
# ---------------------------------------------------------------------------

RATIOS = [0.0, 0.35, 0.5, 0.65, 0.8, 1.0]    # D-07
LEVEL = "1"                                    # D-10: school_anxiety only; headline level = 1
QUESTIONS_PER_QUIZ = 10
EXPERIMENT_SEED = 12345                        # D-08: recorded in CSV header
BOOTSTRAP_SEED = 67890                         # D-17: bootstrap reproducibility

DEFAULT_N_LEARNERS = 50                        # D-08
DEFAULT_N_QUIZZES = 25
FALLBACK_N_LEARNERS = 30                       # D-09
FALLBACK_N_QUIZZES = 20
TINY_N_LEARNERS = 2
TINY_N_QUIZZES = 3

ADAPT_CSV_FIELDS = [
    "timestamp",
    "ratio",
    "learner_seed",
    "quiz_index",
    "mean_mastery",
    "weak_kw_exposure_count",
    "strong_kw_drift",
    "coverage_entropy",
    "weak_set_size",
    "K",
    "level",
    "quizzes_to_mastery",
]


# ---------------------------------------------------------------------------
# Main run loop
# ---------------------------------------------------------------------------

def run_one_learner(learner_seed, ratio, n_quizzes, *,
                    topic, docset_hash, keywords, pool,
                    chunk_vecs_cache, kw_vecs_cache):
    """Simulate one learner through n_quizzes and return per-quiz snapshot rows."""
    from rag.qg import plan_only

    learner = Learner(keywords=keywords, seed=learner_seed, bkt_params=dict(DEFAULT_BKT))
    K = len(keywords)

    history = []
    targets_per_quiz = []
    initially_weak = set(learner.initially_weak)
    initially_strong = set(learner.initially_strong)
    initial_mastery = dict(learner.initial_mastery)

    for quiz_idx in range(1, n_quizzes + 1):
        weak = learner.dynamic_weak_set()
        plan = plan_only(
            topic=topic,
            docset_hash=docset_hash,
            mix={"mcq": QUESTIONS_PER_QUIZ, "yesno": 0},
            keywords=keywords,
            weak_keywords=weak,
            weak_focus_ratio=ratio,
            _chunk_vecs_cache=chunk_vecs_cache,
            _kw_vecs_cache=kw_vecs_cache,
            _pool_cache=pool,
        )
        targeted = plan["targeted_keywords"]
        learner.observe_quiz(targeted)
        history.append(dict(learner.mastery))
        targets_per_quiz.append(targeted)

    qtm = quizzes_to_mastery(history, max_quizzes=n_quizzes)

    rows = []
    for q_idx, state in enumerate(history, start=1):
        mean_mastery = sum(state.values()) / K
        weak_set_size = sum(1 for m in state.values() if m < 0.5)
        exposures_so_far = targets_per_quiz[:q_idx]
        rows.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ratio": ratio,
            "learner_seed": learner_seed,
            "quiz_index": q_idx,
            "mean_mastery": round(mean_mastery, 6),
            "weak_kw_exposure_count": weak_kw_exposure_count(exposures_so_far, initially_weak),
            "strong_kw_drift": round(strong_kw_drift(initial_mastery, state, initially_strong), 6),
            "coverage_entropy": round(coverage_entropy(exposures_so_far, keywords), 6),
            "weak_set_size": weak_set_size,
            "K": K,
            "level": LEVEL,
            "quizzes_to_mastery": qtm,
        })
    return rows


def run_adapt_benchmark(n_learners, n_quizzes, *, write_plot=True):
    from rag.ingest import ingest_topic
    from rag.qg import _ordered_chunks, collection_for, emb_fn

    print("=" * 60)
    print("WLA Adaptive Scheduler Validation — Phase 9")
    print(f"Topic          : {TOPIC} (level {LEVEL})")
    print(f"Ratios         : {RATIOS}")
    print(f"N_learners     : {n_learners}")
    print(f"N_quizzes      : {n_quizzes}")
    print(f"Total sim runs : {n_learners * n_quizzes * len(RATIOS)}")
    print(f"Experiment seed: {EXPERIMENT_SEED}")
    print("=" * 60)

    print("[1/4] Ingesting corpus...")
    res = ingest_topic(TOPIC, force=False)
    docset_hash = res.get("docset_hash", "")
    if not docset_hash:
        print("ERROR: ingest_topic returned no docset_hash")
        return

    print("[2/4] Loading chunks and warming caches...")
    col = collection_for(TOPIC, None)
    pool = _ordered_chunks(col, TOPIC, docset_hash)
    keywords = load_level_keywords(TOPIC, LEVEL)
    chunk_vecs_cache = np.array([emb_fn(txt)[0] for txt, _ in pool])
    kw_vecs_cache = {kw: emb_fn(kw)[0] for kw in keywords}
    print(f"  pool_size={len(pool)}  K={len(keywords)}")

    print("[3/4] Running ratio sweep...")
    rng = np.random.default_rng(EXPERIMENT_SEED)
    learner_seeds = rng.integers(1, 10_000_000, size=n_learners).tolist()

    results = []
    total_learners = len(RATIOS) * n_learners
    done = 0
    for ratio in RATIOS:
        for ls in learner_seeds:
            results.extend(run_one_learner(
                learner_seed=int(ls),
                ratio=ratio,
                n_quizzes=n_quizzes,
                topic=TOPIC, docset_hash=docset_hash,
                keywords=keywords, pool=pool,
                chunk_vecs_cache=chunk_vecs_cache,
                kw_vecs_cache=kw_vecs_cache,
            ))
            done += 1
        print(f"  ratio={ratio}  done={done}/{total_learners}")

    print("[4/4] Writing CSV and plot...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_csv = RESULTS_DIR / f"adapt_{ts}.csv"
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        f.write(
            f"# phase9_seed={EXPERIMENT_SEED} ratios={RATIOS} "
            f"n_learners={n_learners} n_quizzes={n_quizzes} "
            f"bootstrap_seed={BOOTSTRAP_SEED} topic={TOPIC} level={LEVEL} "
            f"ts={ts} pythonhashseed={__import__('os').environ.get('PYTHONHASHSEED', '')}\n"
        )
        writer = csv.DictWriter(f, fieldnames=ADAPT_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(results)
    print(f"CSV  -> {output_csv}  ({len(results)} rows)")

    if write_plot:
        from benchmarks.adapt.plots import render_learning_curve
        png_path = RESULTS_DIR / f"adapt_learning_curve_{ts}.png"
        render_learning_curve(
            csv_path=output_csv,
            output_path=png_path,
            ratios=RATIOS,
            bootstrap_seed=BOOTSTRAP_SEED,
        )
        print(f"PNG  -> {png_path}")

    return output_csv


def main():
    ap = argparse.ArgumentParser(description="WLA Adaptive Scheduler Validation runner")
    ap.add_argument("--tiny", action="store_true",
                    help="Tiny run: 2 learners x 3 quizzes. For integration tests only.")
    ap.add_argument("--smoke", action="store_true",
                    help="Alias for --tiny — runtime smoke check.")
    ap.add_argument("--fallback", action="store_true",
                    help="Use D-09 fallback sample size (30 learners x 20 quizzes)")
    ap.add_argument("--no-plot", action="store_true",
                    help="Skip the plot step (CSV only)")
    args = ap.parse_args()

    if args.tiny or args.smoke:
        n_learners, n_quizzes = TINY_N_LEARNERS, TINY_N_QUIZZES
    elif args.fallback:
        n_learners, n_quizzes = FALLBACK_N_LEARNERS, FALLBACK_N_QUIZZES
    else:
        n_learners, n_quizzes = DEFAULT_N_LEARNERS, DEFAULT_N_QUIZZES

    run_adapt_benchmark(n_learners, n_quizzes, write_plot=not args.no_plot)


if __name__ == "__main__":
    main()
