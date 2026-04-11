#!/usr/bin/env python3
"""
RAGAS + rubric scoring script for LLM benchmark results.

Reads a completed llm_*.csv (from llm_benchmark.py), joins retrieval contexts
from the corresponding rag_*.csv, and scores each row with:
  - RAGAS faithfulness (Gemini 2.5 Flash Lite judge)
  - Rubric-based MCQ quality (see benchmarks/scoring/rubric.py): stem_clarity,
    distractor_plausibility, pedagogical_appropriateness, mcq_quality

Updates the CSV in-place with faithfulness, the four rubric columns, and
composite_score (v2 formula: 0.4 faith + 0.3 ctx + 0.2 mcq_quality + 0.1 fmt).

NOTE: RAGAS answer_relevancy was removed from the active metric set after
Finding 4 showed it was a weak discriminator on MCQ-generation tasks; the
column is retained in the CSV schema for backward-compat with pre-Finding-5
runs, and the code is commented out rather than deleted so it can be
re-enabled for investigation.

Usage:
  cd services && python -m benchmarks.llm_ragas_score
  cd services && python -m benchmarks.llm_ragas_score --llm-csv llm_20260410_191454.csv
  cd services && python -m benchmarks.llm_ragas_score --llm-csv llm_20260410_191454.csv --rag-csv rag_20260410_160216.csv

Requirements:
  - GOOGLE_API_KEY set in .env or environment
  - ragas, langchain-google-genai, sentence-transformers installed
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from benchmarks.config import LLM_CSV_FIELDS
from benchmarks.io import build_context_lookup, find_latest_csv, load_csv, save_csv
from benchmarks.parsing import extract_json
from benchmarks.scoring import rubric
from benchmarks.scoring.composite import composite_score
from benchmarks.scoring.judge import build_gemini_judge

BATCH_SIZE = 5


# ---------------------------------------------------------------------------
# RAGAS scoring in batches
# ---------------------------------------------------------------------------

def score_batch(batch: list[dict], judge_llm) -> list[dict]:
    """Score a batch of rows with RAGAS faithfulness + MCQ rubric.

    Returns a list of dicts containing faithfulness and the four rubric
    fields. answer_relevancy is no longer computed (see Finding 4); the
    RAGAS code path is preserved as comments for re-enabling if needed.
    """
    from datasets import Dataset
    from ragas import evaluate as ragas_evaluate
    from ragas.metrics import faithfulness
    # from ragas.metrics import answer_relevancy  # disabled — see Finding 4
    from ragas.run_config import RunConfig

    faithfulness.llm = judge_llm
    # answer_relevancy.llm = judge_llm
    # answer_relevancy.embeddings = embeddings

    run_cfg = RunConfig(max_workers=1, timeout=180)

    data = {
        "question": [r["question"] for r in batch],
        "contexts": [r["_contexts"] for r in batch],
        "answer": [r["generated_answer"] for r in batch],
        "ground_truth": [r["ground_truth"] for r in batch],
    }
    dataset = Dataset.from_dict(data)

    max_attempts = 3
    faith_scores = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = ragas_evaluate(
                dataset,
                metrics=[faithfulness],  # answer_relevancy disabled
                run_config=run_cfg,
            )
            df = result.to_pandas()
            faith_scores = [float(df["faithfulness"].iloc[i]) for i in range(len(batch))]
            break
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt < max_attempts:
                wait = 30 * attempt
                print(f"  Rate limited (429), waiting {wait}s (attempt {attempt}/{max_attempts})...")
                time.sleep(wait)
                continue
            raise

    # Rubric scoring: one direct Gemini call per row, reusing the same judge.
    raw_llm = getattr(judge_llm, "langchain_llm", judge_llm)
    empty_rubric = {
        "stem_clarity": None,
        "distractor_plausibility": None,
        "pedagogical_appropriateness": None,
        "mcq_quality": None,
    }
    results = []
    for i, r in enumerate(batch):
        row_scores = {
            "faithfulness": faith_scores[i],
            "answer_relevancy": None,  # Finding 4
            **dict(empty_rubric),
        }
        parsed = extract_json(r.get("raw_output", ""))
        mcq = rubric.parse_mcq(parsed)
        if mcq is not None:
            scores = rubric.score_mcq(raw_llm, mcq, r.get("_contexts", []))
            if scores:
                row_scores.update(scores)
        results.append(row_scores)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_scoring(llm_csv_path: str | None = None, rag_csv_path: str | None = None, force: bool = False):
    llm_path = find_latest_csv("llm", llm_csv_path)
    rag_path = find_latest_csv("rag", rag_csv_path)

    llm_rows = load_csv(llm_path)
    rag_rows = load_csv(rag_path)
    context_lookup = build_context_lookup(rag_rows)

    # Filter to rows that need scoring (have generated_answer but no valid faithfulness)
    to_score = []
    for r in llm_rows:
        if not r.get("generated_answer"):
            continue
        if not force:
            f = r.get("faithfulness", "")
            if f and f not in ("", "None") and f.lower() != "nan":
                continue
        key = (r["emb_model"], r["chunk_size"], r["chunk_overlap"], r["retrieval_type"], r["question"])
        contexts = context_lookup.get(key, [])
        if not contexts:
            print(f"  Warning: no contexts found for {r['generator_model']} / {r['question'][:40]}...")
            continue
        r["_contexts"] = contexts
        to_score.append(r)

    total = len(to_score)
    already_scored = len([
        r for r in llm_rows
        if r.get("faithfulness") and r["faithfulness"] not in ("", "None") and r["faithfulness"].lower() != "nan"
    ])

    print("=" * 60)
    print("WLA LLM RAGAS Scoring")
    print(f"LLM CSV     : {llm_path.name}  ({len(llm_rows)} rows)")
    print(f"RAG CSV     : {rag_path.name}")
    print(f"Already scored : {already_scored}")
    print(f"To score    : {total}")
    print(f"Batch size  : {BATCH_SIZE}")
    print("=" * 60)

    if total == 0:
        print("Nothing to score.")
        return

    print("\nSetting up Gemini judge...")
    judge_llm = build_gemini_judge()
    if judge_llm is None:
        print("ERROR: Gemini judge unavailable (GOOGLE_API_KEY not set or setup failed)")
        sys.exit(1)
    print("  ✓ Google gemini-2.5-flash-lite")
    # MiniLM embeddings were previously required by answer_relevancy (disabled — see Finding 4).

    scored = 0
    for batch_start in range(0, total, BATCH_SIZE):
        batch = to_score[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n  Batch {batch_num}/{total_batches} ({len(batch)} rows)...")

        try:
            results = score_batch(batch, judge_llm)
            for r, scores in zip(batch, results):
                r["faithfulness"] = scores["faithfulness"]
                r["answer_relevancy"] = scores["answer_relevancy"]  # None — Finding 4
                r["stem_clarity"] = scores["stem_clarity"]
                r["distractor_plausibility"] = scores["distractor_plausibility"]
                r["pedagogical_appropriateness"] = scores["pedagogical_appropriateness"]
                r["mcq_quality"] = scores["mcq_quality"]
                ctx_rel = float(r["context_relevancy"]) if r.get("context_relevancy") and r["context_relevancy"] not in ("", "None") else None
                fmt = float(r["format_compliance"]) if r.get("format_compliance") else 0.0
                r["composite_score"] = composite_score(
                    scores["faithfulness"], ctx_rel, scores["mcq_quality"], fmt,
                )
                scored += 1
                mcq_q_str = f"{scores['mcq_quality']:.3f}" if scores['mcq_quality'] is not None else "n/a"
                print(f"    ✓ faith={scores['faithfulness']:.3f}  mcq_q={mcq_q_str}")
        except Exception as e:
            print(f"    ✗ Batch failed: {type(e).__name__}: {e}")
            print(f"    Saving progress so far ({scored} scored)...")
            break

        # Save after each batch
        save_csv(llm_path, llm_rows, LLM_CSV_FIELDS)
        print(f"    Saved to {llm_path.name}")

    # Clean up internal field
    for r in llm_rows:
        r.pop("_contexts", None)

    # Final save
    save_csv(llm_path, llm_rows, LLM_CSV_FIELDS)

    print(f"\n{'=' * 60}")
    print(f"Scored {scored}/{total} rows")
    print(f"Results saved to {llm_path.name}")

    # Print summary by model
    from collections import defaultdict
    model_scores = defaultdict(list)
    for r in llm_rows:
        if r.get("composite_score") and r["composite_score"] not in ("", "None"):
            model_scores[r["generator_model"]].append(float(r["composite_score"]))

    if model_scores:
        print(f"\n{'─' * 60}")
        print("Mean composite score by generator:")
        for model, scores in sorted(model_scores.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True):
            print(f"  {model:20s}  {sum(scores)/len(scores):.4f}  (n={len(scores)})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAGAS scoring for LLM benchmark results")
    parser.add_argument("--llm-csv", help="LLM results CSV to score (default: latest)")
    parser.add_argument("--rag-csv", help="RAG results CSV for contexts (default: latest)")
    parser.add_argument("--force", action="store_true", help="Re-score all rows, ignoring existing scores")
    args = parser.parse_args()

    run_scoring(args.llm_csv, args.rag_csv, force=args.force)
