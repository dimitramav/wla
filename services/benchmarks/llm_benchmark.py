#!/usr/bin/env python3
"""
LLM generation benchmarking script for Watch-Listen-Act.

Tests generator models against frozen RAG retrieval contexts to evaluate
question generation quality. Each model generates quiz questions from the
same retrieved chunks, ensuring fair comparison.

Evaluates with Google Gemini 2.5 Flash Lite as RAGAS judge (Zheng et al., 2023)
to avoid small-model self-grading bias.

Inputs:
  services/benchmarks/results/rag_*.csv — frozen retrieval contexts from rag_benchmark.py

Outputs:
  services/benchmarks/results/llm_YYYYMMDD_HHMMSS.csv — one row per question per config
  Top-3 configurations printed to stdout

Usage:
  cd services && python -m benchmarks.llm_benchmark
  cd services && python -m benchmarks.llm_benchmark --rag-csv results/rag_20260410_160216.csv

Requirements:
  - services/requirements.txt dependencies installed
  - Ollama running at http://localhost:11434
  - GOOGLE_API_KEY set in .env or environment (for RAGAS judge)
"""

import csv
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from benchmarks.config import GENERATOR_MODELS, LLM_CSV_FIELDS
from benchmarks.io import RESULTS_DIR, find_latest_csv, load_csv
from benchmarks.parsing import extract_json, validate_format
from benchmarks.scoring import rubric
from benchmarks.scoring.rubric import score_text_independence
from benchmarks.scoring.composite import composite_score
from benchmarks.scoring.judge import build_gemini_judge
from llm.prompts import SYSTEM_QG as SYSTEM_PROMPT
from llm.prompts import USER_QG_MC_TEMPLATE, DIFFICULTY_INSTRUCTIONS

OLLAMA_URL = os.getenv("LLM_URL", "http://localhost:11434")

# ---------------------------------------------------------------------------
# Ollama model management (pull/rm for disk space)
# ---------------------------------------------------------------------------

def ollama_pull(tag: str) -> bool:
    print(f"    Pulling {tag}...")
    try:
        result = subprocess.run(
            ["ollama", "pull", tag],
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode == 0:
            print(f"    ✓ {tag} ready")
            return True
        print(f"    ✗ Pull failed: {result.stderr.strip()}")
        return False
    except Exception as e:
        print(f"    ✗ Pull error: {e}")
        return False


def ollama_rm(tag: str):
    try:
        subprocess.run(
            ["ollama", "rm", tag],
            capture_output=True, text=True, timeout=60,
        )
        print(f"    Removed {tag}")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# LLM generation
# ---------------------------------------------------------------------------

def generate_question(model_tag: str, contexts: list[str], difficulty_label: str = "beginner") -> tuple[str, float]:
    """Generate a quiz question from contexts. Returns (raw_output, latency_seconds)."""
    import requests

    excerpt = "\n\n---\n\n".join(contexts)
    difficulty_instructions = DIFFICULTY_INSTRUCTIONS.get(difficulty_label, DIFFICULTY_INSTRUCTIONS["beginner"])
    user_prompt = USER_QG_MC_TEMPLATE.format(
        excerpt=excerpt,
        difficulty_label=difficulty_label,
        difficulty_instructions=difficulty_instructions,
    )

    payload = {
        "model": model_tag,
        "options": {"seed": 7, "temperature": 0.0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }

    start = time.time()
    r = requests.post(f"{OLLAMA_URL}/v1/chat/completions", json=payload, timeout=600)
    latency = time.time() - start

    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"]
    return raw, round(latency, 2)


# ---------------------------------------------------------------------------
# RAGAS evaluation with Gemini judge
# ---------------------------------------------------------------------------

def evaluate_with_ragas(rows: list, judge_llm) -> list[dict]:
    """Evaluate faithfulness for generated answers.

    Uses batched RAGAS evaluation with Gemini judge. Includes retry logic
    for rate limiting (HTTP 429).

    Returns list of {"faithfulness": float|None, "answer_relevancy": None}.

    NOTE: answer_relevancy was removed from the RAGAS metric set after
    Finding 4 showed it was a weak discriminator on MCQ-generation tasks.
    The column is still written (as None for new runs) for backward-compat
    with older CSVs. MCQ-side quality is now captured by the rubric metric
    (see benchmarks/scoring/rubric.py and Finding 5).
    """
    n = len(rows)
    if judge_llm is None:
        return [{"faithfulness": None, "answer_relevancy": None}] * n

    try:
        from datasets import Dataset
        from ragas import evaluate as ragas_evaluate
        from ragas.metrics import faithfulness
        # from ragas.metrics import answer_relevancy  # disabled — see Finding 4
        from ragas.run_config import RunConfig

        faithfulness.llm = judge_llm
        # answer_relevancy.llm = judge_llm
        # answer_relevancy.embeddings = ...  # would need MiniLM wrapper

        # Sequential to respect Gemini rate limits (free tier)
        run_cfg = RunConfig(max_workers=1, timeout=120)

        questions = [r["question"] for r in rows]
        contexts = [r["contexts"] for r in rows]
        answers = [r["generated_answer"] for r in rows]
        ground_truths = [r["ground_truth"] for r in rows]

        data = {
            "question": questions,
            "contexts": contexts,
            "answer": answers,
            "ground_truth": ground_truths,
        }
        dataset = Dataset.from_dict(data)

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                result = ragas_evaluate(
                    dataset,
                    metrics=[faithfulness],  # answer_relevancy disabled — see Finding 4
                    run_config=run_cfg,
                )
                df = result.to_pandas()
                return [
                    {
                        "faithfulness": float(df["faithfulness"].iloc[i]),
                        "answer_relevancy": None,
                    }
                    for i in range(n)
                ]
            except Exception as e:
                err_str = str(e)
                if "429" in err_str and attempt < max_attempts:
                    wait = 30 * attempt
                    print(f"    Rate limited (429), waiting {wait}s (attempt {attempt}/{max_attempts})...")
                    time.sleep(wait)
                    continue
                raise

    except Exception as e:
        print(f"  ⚠ RAGAS evaluation failed: {type(e).__name__}: {e}")
        return [{"faithfulness": None, "answer_relevancy": None}] * n


def evaluate_with_rubric(rows: list, judge_llm) -> list[dict]:
    """Score each row's generated MCQ with the Gemini rubric judge.

    Uses the raw ChatGoogleGenerativeAI under the RAGAS wrapper
    (accessed via .langchain_llm) rather than the RAGAS wrapper itself,
    because the rubric is a plain LLM call, not a RAGAS metric.

    Returns list of {"stem_clarity", "distractor_plausibility",
    "pedagogical_appropriateness", "mcq_quality"} dicts (or all-None on
    failure / unparseable MCQ).
    """
    n = len(rows)
    empty = {
        "stem_clarity": None,
        "distractor_plausibility": None,
        "pedagogical_appropriateness": None,
        "mcq_quality": None,
    }
    if judge_llm is None:
        return [dict(empty) for _ in range(n)]

    raw_llm = getattr(judge_llm, "langchain_llm", judge_llm)

    results = []
    for i, r in enumerate(rows):
        parsed = extract_json(r.get("raw_output", ""))
        mcq = rubric.parse_mcq(parsed)
        if mcq is None:
            results.append(dict(empty))
            continue
        scores = rubric.score_mcq(raw_llm, mcq, r.get("contexts", []))
        results.append(scores if scores else dict(empty))
        if (i + 1) % 10 == 0:
            print(f"    rubric {i+1}/{n}")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_benchmarks(rag_csv_path: str | None = None, resume_from: int = 1):
    csv_path = find_latest_csv("rag", rag_csv_path)
    rag_rows = load_csv(csv_path)

    n_questions = len(rag_rows)
    n_models = len(GENERATOR_MODELS)
    n_configs = len(set(
        (r["emb_model"], r["chunk_size"], r["chunk_overlap"], r["retrieval_type"])
        for r in rag_rows
    ))

    print("=" * 60)
    print("WLA LLM Generation Benchmarking Suite")
    print(f"RAG source  : {csv_path.name}")
    print(f"RAG rows    : {n_questions} ({n_configs} configs × {n_questions // max(n_configs, 1)} questions)")
    print(f"Generators  : {n_models} models")
    print(f"Total evals : {n_questions * n_models}")
    if resume_from > 1:
        print(f"Resuming    : from model {resume_from}/{n_models}")
    print("=" * 60)

    # Build Gemini judge
    judge_llm = build_gemini_judge()
    if judge_llm:
        print("RAGAS Judge : Google gemini-2.5-flash-lite ✓")
    else:
        print("RAGAS Judge : unavailable — faithfulness/answer_relevancy will be None")

    all_results = []
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_csv = RESULTS_DIR / f"llm_{ts}.csv"

    for model_idx, model in enumerate(GENERATOR_MODELS, 1):
        if model_idx < resume_from:
            print(f"\n  [{model_idx}/{n_models}] {model['name']} — SKIPPED (resume)")
            continue

        model_name = model["name"]
        model_tag = model["tag"]

        print(f"\n{'═' * 60}")
        print(f"  [{model_idx}/{n_models}] Generator: {model_name} ({model_tag})")
        print(f"{'═' * 60}")

        # Pull model if needed
        if model["pull_needed"]:
            if not ollama_pull(model_tag):
                print(f"  ✗ Skipping {model_name} — pull failed")
                continue

        # Generate for each RAG row
        model_rows = []
        for i, rag_row in enumerate(rag_rows):
            contexts_raw = rag_row.get("contexts_text", "")
            contexts = contexts_raw.split("|||") if contexts_raw else []
            difficulty_label = rag_row.get("difficulty_label", "beginner")

            row = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "generator_model": model_name,
                "emb_model": rag_row["emb_model"],
                "chunk_size": rag_row["chunk_size"],
                "chunk_overlap": rag_row["chunk_overlap"],
                "retrieval_type": rag_row["retrieval_type"],
                "question": rag_row["question"],
                "ground_truth": rag_row.get("ground_truth", ""),
                "difficulty_label": difficulty_label,
                "contexts": contexts,  # kept for RAGAS, not written to CSV
                "format_compliance": 0.0,
                "response_time_s": None,
                "raw_output": "",
                "generated_answer": "",
                "faithfulness": None,
                "answer_relevancy": None,
                "stem_clarity": None,
                "distractor_plausibility": None,
                "pedagogical_appropriateness": None,
                "mcq_quality": None,
                "text_independence": None,
                "context_relevancy": rag_row.get("context_relevancy"),
                "composite_score": None,
            }

            try:
                raw, latency = generate_question(model_tag, contexts, difficulty_label)
                row["raw_output"] = raw
                row["response_time_s"] = latency

                parsed = extract_json(raw)
                row["format_compliance"] = validate_format(parsed)

                if parsed and isinstance(parsed, dict):
                    # Use the generated question text + explanation as the "answer"
                    # for RAGAS evaluation
                    q_text = parsed.get("text", "")
                    why = parsed.get("why", "")
                    options = parsed.get("options", [])
                    correct = parsed.get("correct", "")
                    correct_text = ""
                    for opt in options:
                        if opt.startswith(f"{correct})"):
                            correct_text = opt
                            break
                    row["generated_answer"] = (
                        f"Question: {q_text}\n"
                        f"Correct answer: {correct_text}\n"
                        f"Explanation: {why}"
                    )

            except Exception as e:
                row["raw_output"] = f"ERROR: {e}"
                row["response_time_s"] = None
                row["format_compliance"] = 0.0

            row["text_independence"] = score_text_independence(row["raw_output"])
            model_rows.append(row)
            status = "✓" if row["format_compliance"] == 1.0 else "✗"
            print(f"    {status} [{i+1}/{n_questions}] {row['response_time_s']}s  fmt={row['format_compliance']}")

        # RAGAS evaluation for this model's outputs
        valid_rows = [r for r in model_rows if r["generated_answer"]]
        if valid_rows and judge_llm:
            print(f"\n    Running RAGAS evaluation ({len(valid_rows)} valid answers)...")
            ragas_results = evaluate_with_ragas(valid_rows, judge_llm)
            for r, scores in zip(valid_rows, ragas_results):
                r["faithfulness"] = scores["faithfulness"]
                r["answer_relevancy"] = scores["answer_relevancy"]  # None — Finding 4

            print(f"    Running MCQ rubric scoring ({len(valid_rows)} rows)...")
            rubric_results = evaluate_with_rubric(valid_rows, judge_llm)
            for r, scores in zip(valid_rows, rubric_results):
                r["stem_clarity"] = scores["stem_clarity"]
                r["distractor_plausibility"] = scores["distractor_plausibility"]
                r["pedagogical_appropriateness"] = scores["pedagogical_appropriateness"]
                r["mcq_quality"] = scores["mcq_quality"]

        # Compute composite scores
        for r in model_rows:
            ctx_rel = float(r["context_relevancy"]) if r["context_relevancy"] is not None else None
            ti = float(r["text_independence"]) if r["text_independence"] is not None else None
            r["composite_score"] = composite_score(
                r["faithfulness"], ctx_rel, r["mcq_quality"], ti, r["format_compliance"],
            )

        all_results.extend(model_rows)

        # Save incrementally after each model
        needs_header = not output_csv.exists() or output_csv.stat().st_size == 0
        with open(output_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LLM_CSV_FIELDS)
            if needs_header:
                writer.writeheader()
            for r in model_rows:
                write_row = {k: r.get(k) for k in LLM_CSV_FIELDS}
                writer.writerow(write_row)
        print(f"    Saved {len(model_rows)} rows to {output_csv.name}  (total: {len(all_results)})")

        # Remove model to free disk space
        if model["pull_needed"]:
            ollama_rm(model_tag)

    # Final summary
    print(f"\n{'=' * 60}")
    if all_results:
        print(f"Results written to {output_csv}  ({len(all_results)} rows)")

        # Top-3 configurations by mean composite score
        print(f"\n{'─' * 60}")
        print("Top-3 Configurations (by mean composite score)")
        print(f"{'─' * 60}")
        _print_top_configs(all_results)
    else:
        print("No results to write — check errors above.")


def _print_top_configs(results: list):
    """Aggregate and print top-3 configurations by mean composite score."""
    from collections import defaultdict

    config_scores = defaultdict(list)
    for r in results:
        if r["composite_score"] is not None:
            key = (
                r["generator_model"],
                r["emb_model"],
                r["chunk_size"],
                r["chunk_overlap"],
                r["retrieval_type"],
            )
            config_scores[key].append(r["composite_score"])

    if not config_scores:
        print("  No composite scores available (RAGAS evaluation may have been skipped)")
        return

    ranked = sorted(
        config_scores.items(),
        key=lambda x: sum(x[1]) / len(x[1]),
        reverse=True,
    )

    for rank, (key, scores) in enumerate(ranked[:3], 1):
        gen, emb, cs, co, ret = key
        mean = sum(scores) / len(scores)
        emb_short = emb.split("/")[-1] if "/" in emb else emb
        print(f"  #{rank}  {mean:.4f}  {gen} | {emb_short} {cs}/{co} {ret}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WLA LLM Generation Benchmark")
    parser.add_argument("--rag-csv", help="Path to specific RAG results CSV (default: latest)")
    parser.add_argument("--resume", type=int, default=1,
                        help="Model number to resume from (e.g. --resume 3 skips models 1-2)")
    args = parser.parse_args()

    run_benchmarks(args.rag_csv, resume_from=args.resume)
