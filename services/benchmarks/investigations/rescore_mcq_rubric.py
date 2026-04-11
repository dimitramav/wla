#!/usr/bin/env python3
"""
Offline rubric-based MCQ quality rescoring.

Adds a task-specific MCQ quality signal to complement RAGAS answer-side
metrics, which were shown to be weak discriminators on this task (see
LLM_BENCHMARK_REPORT.md Finding 4; the 0.35-0.38 cluster is a real property
of the task under production MiniLM embeddings, not a payload artefact).

The judge (Gemini 2.5 Flash Lite) rates each generated MCQ on three
MCQ-specific dimensions, each 1-5:
  - stem_clarity               : is the question well-formed and unambiguous?
  - distractor_plausibility    : are the 3 wrong options plausible-but-wrong?
  - pedagogical_appropriateness: does it probe understanding, not rote recall?

mcq_quality = mean(three dimensions) / 5   (normalised to 0..1)

The rubric is adapted from the Med-PaLM clinical QA evaluation protocol
(Singhal et al., 2023) and targets the MCQ-specific quality dimensions
identified by Kurdi et al. (2020) in their systematic review of automatic
question generation for educational purposes.

Usage:
  cd services && python -m benchmarks.investigations.rescore_mcq_rubric \\
      --llm-csv results/llm_20260410_191454.csv \\
      --rag-csv results/rag_20260410_160216.csv
  cd services && python -m benchmarks.investigations.rescore_mcq_rubric \\
      --llm-csv results/llm_20260410_191454.csv \\
      --rag-csv results/rag_20260410_160216.csv \\
      --limit 10
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from benchmarks.io import RESULTS_DIR
from benchmarks.parsing import extract_json
from benchmarks.scoring import rubric
from benchmarks.scoring.composite import composite_score


def build_judge():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=api_key,
        temperature=0.0,
        max_retries=3,
    )


def load_context_lookup(rag_csv: Path) -> dict:
    lookup = {}
    with open(rag_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (
                row["emb_model"],
                row["chunk_size"],
                row["chunk_overlap"],
                row["retrieval_type"],
                row["question"],
            )
            contexts_raw = row.get("contexts_text", "")
            lookup[key] = contexts_raw.split("|||") if contexts_raw else []
    return lookup


def _fnum(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s in ("None", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def rescore(llm_csv: Path, rag_csv: Path, out_csv: Path, limit: int | None = None):
    ctx_lookup = load_context_lookup(rag_csv)

    with open(llm_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} llm rows from {llm_csv.name}")

    judge = build_judge()
    print("✓ Gemini 2.5 Flash Lite judge ready\n")

    new_cols = [
        "stem_clarity",
        "distractor_plausibility",
        "pedagogical_appropriateness",
        "mcq_quality",
        "composite_score_v2",
    ]
    out_fields = list(rows[0].keys()) + new_cols

    scored_count = 0
    failed_count = 0
    t_start = time.time()

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()

        for i, r in enumerate(rows):
            out = dict(r)
            for k in new_cols:
                out[k] = ""

            if limit is not None and scored_count >= limit:
                writer.writerow(out)
                continue

            parsed = extract_json(r.get("raw_output", "") or "")
            mcq = rubric.parse_mcq(parsed)
            if not mcq:
                failed_count += 1
                writer.writerow(out)
                continue

            key = (
                r["emb_model"],
                r["chunk_size"],
                r["chunk_overlap"],
                r["retrieval_type"],
                r["question"],
            )
            context = ctx_lookup.get(key, [])

            scores = rubric.score_mcq(judge, mcq, context)
            if scores:
                out["stem_clarity"] = scores["stem_clarity"]
                out["distractor_plausibility"] = scores["distractor_plausibility"]
                out["pedagogical_appropriateness"] = scores["pedagogical_appropriateness"]
                out["mcq_quality"] = scores["mcq_quality"]
                out["composite_score_v2"] = composite_score(
                    _fnum(r.get("faithfulness")),
                    _fnum(r.get("context_relevancy")),
                    scores["mcq_quality"],
                    _fnum(r.get("format_compliance")),
                )
                scored_count += 1
                if scored_count % 10 == 0 or scored_count <= 5:
                    elapsed = time.time() - t_start
                    rate = scored_count / elapsed if elapsed > 0 else 0
                    print(f"  [{scored_count:>3}] row {i+1:>3}/{len(rows)}  "
                          f"{r['generator_model']:<14}  "
                          f"stem={scores['stem_clarity']} "
                          f"dstr={scores['distractor_plausibility']} "
                          f"ped={scores['pedagogical_appropriateness']}  "
                          f"mcq_q={scores['mcq_quality']:.3f}  "
                          f"({rate:.1f} row/s)")
            else:
                failed_count += 1

            writer.writerow(out)

    total_time = time.time() - t_start
    print(f"\nWrote {out_csv}")
    print(f"  scored       : {scored_count}")
    print(f"  failed/skipped: {failed_count}")
    print(f"  wall time    : {total_time/60:.1f} min")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rubric-based MCQ quality rescoring")
    parser.add_argument("--llm-csv", required=True, help="Path to llm_*.csv")
    parser.add_argument("--rag-csv", required=True, help="Path to the frozen rag_*.csv")
    parser.add_argument("--out-csv", help="Output CSV path (default: <llm-csv>_mcq_rubric.csv)")
    parser.add_argument("--limit", type=int, help="Smoke test: only score first N parseable rows")
    args = parser.parse_args()

    def _resolve(p: str) -> Path:
        pp = Path(p)
        if pp.is_absolute() or pp.exists():
            return pp
        return RESULTS_DIR / pp.name

    llm_path = _resolve(args.llm_csv)
    rag_path = _resolve(args.rag_csv)
    out_path = _resolve(args.out_csv) if args.out_csv else llm_path.with_name(
        llm_path.stem + "_mcq_rubric.csv"
    )

    rescore(llm_path, rag_path, out_path, limit=args.limit)
