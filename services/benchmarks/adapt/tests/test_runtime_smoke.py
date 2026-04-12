"""Runtime smoke test — gates the D-08 / D-09 decision.

Runs 1 learner x 25 quizzes with cached chunk/keyword embeddings and
extrapolates to 7,500 calls. If the extrapolated total exceeds 300 s (D-09
budget), prints a FALLBACK instruction — Plan 03 runner must use
N_LEARNERS=30, N_QUIZZES=20 (D-09) instead of 50x25 (D-08).

This test is non-strict: it always exits 0 so CI does not flap when the
default 50x25 is just marginal. The budget decision is captured in stdout.
"""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rag.qg import (
    plan_only, _ordered_chunks, collection_for, emb_fn,
)
from rag.ingest import ingest_topic
from benchmarks.adapt.learner import Learner, load_level_keywords

TOPIC = "school_anxiety"
LEVEL = "1"
N_QUIZZES = 25
QUESTIONS_PER_QUIZ = 10
FULL_RUN_CALLS = 50 * 25 * 6   # D-08: 7,500
BUDGET_S = 300                 # D-09: 5 minutes


def test_runtime_smoke_extrapolation(capsys):
    res = ingest_topic(TOPIC, force=False)
    docset_hash = res.get("docset_hash", "")
    assert docset_hash, "ingest_topic returned no docset_hash"

    col = collection_for(TOPIC, None)
    pool = _ordered_chunks(col, TOPIC, docset_hash)
    assert pool, "empty chunk pool — check ingest"

    keywords = load_level_keywords(TOPIC, LEVEL)

    chunk_vecs_cache = np.array([emb_fn(txt)[0] for txt, _ in pool])
    kw_vecs_cache = {kw: emb_fn(kw)[0] for kw in keywords}

    learner = Learner(keywords=keywords, seed=0)

    t0 = time.perf_counter()
    for _ in range(N_QUIZZES):
        weak = learner.dynamic_weak_set()
        plan_only(
            topic=TOPIC,
            docset_hash=docset_hash,
            mix={"mcq": QUESTIONS_PER_QUIZ, "yesno": 0},
            keywords=keywords,
            weak_keywords=weak,
            weak_focus_ratio=0.65,
            _chunk_vecs_cache=chunk_vecs_cache,
            _kw_vecs_cache=kw_vecs_cache,
            _pool_cache=pool,
        )
    elapsed = time.perf_counter() - t0

    per_call_s = elapsed / N_QUIZZES
    extrapolated = per_call_s * FULL_RUN_CALLS

    print(f"\nruntime_smoke: {N_QUIZZES} calls in {elapsed:.2f}s "
          f"=> {per_call_s*1000:.1f} ms/call, extrapolated_full={extrapolated:.1f}s")

    if extrapolated > BUDGET_S:
        print(f"runtime_smoke: FALLBACK — extrapolated {extrapolated:.0f}s > {BUDGET_S}s. "
              f"Plan 03 runner must use N_LEARNERS=30, N_QUIZZES=20 (D-09).")
    else:
        print(f"runtime_smoke: OK — under {BUDGET_S}s budget.")
