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
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ---------------------------------------------------------------------------
# Generator models — all local Ollama, Q4 quantized
# ---------------------------------------------------------------------------
GENERATOR_MODELS = [
    {
        "name": "mistral-7b",
        "tag": "mistral:7b-instruct-q4_0",
        "pull_needed": True,  # pull/rm like others to conserve disk space
    },
    {
        "name": "llama3.1-8b",
        "tag": "llama3.1:8b-instruct-q4_0",
        "pull_needed": True,
    },
    {
        "name": "gemma2-9b",
        "tag": "gemma2:9b-instruct-q4_0",
        "pull_needed": True,
    },
    {
        "name": "phi3.5-3.8b",
        "tag": "phi3.5:3.8b-mini-instruct-q4_0",
        "pull_needed": True,
    },
]

OLLAMA_URL = os.getenv("LLM_URL", "http://localhost:11434")
RESULTS_DIR = Path(__file__).parent / "results"

# ---------------------------------------------------------------------------
# Prompt template (matches production prompts.py — MCQ generation)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a careful assessment item writer.
You write questions ONLY from the provided excerpt. Do not invent facts.
Always output strict JSON that conforms to the requested schema."""

USER_PROMPT_TEMPLATE = """Write exactly ONE multiple-choice question from this excerpt.

EXCERPT:
\"\"\"{excerpt}\"\"\"

Rules:
- The question and all answer options must be grammatically correct, well-formed English.
- Base the question ONLY on the excerpt.
- Options must be short and plausible; exactly 4 options labeled A) B) C) D).
- Exactly ONE correct answer; respond with letter only in "correct".
- "why" must be a complete sentence, max 140 characters, grounded in the excerpt.

Return JSON:
{{
  "kind": "mcq",
  "text": "...",
  "options": ["A) ...","B) ...","C) ...","D) ..."],
  "correct": "A"|"B"|"C"|"D",
  "why": "..."
}}"""

REQUIRED_KEYS = {"text", "options", "correct", "why"}

# ---------------------------------------------------------------------------
# CSV columns
# ---------------------------------------------------------------------------
CSV_FIELDS = [
    "timestamp",
    "generator_model",
    "emb_model",
    "chunk_size",
    "chunk_overlap",
    "retrieval_type",
    "question",
    "ground_truth",
    "format_compliance",
    "response_time_s",
    "raw_output",
    "generated_answer",
    "faithfulness",
    "answer_relevancy",  # retained for backward-compat; no longer used in composite (Finding 4/5)
    "stem_clarity",
    "distractor_plausibility",
    "pedagogical_appropriateness",
    "mcq_quality",
    "context_relevancy",
    "composite_score",
]


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

def generate_question(model_tag: str, contexts: list[str]) -> tuple[str, float]:
    """Generate a quiz question from contexts. Returns (raw_output, latency_seconds)."""
    import requests

    excerpt = "\n\n---\n\n".join(contexts)
    user_prompt = USER_PROMPT_TEMPLATE.format(excerpt=excerpt)

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
    r = requests.post(f"{OLLAMA_URL}/v1/chat/completions", json=payload, timeout=180)
    latency = time.time() - start

    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"]
    return raw, round(latency, 2)


def extract_json(text: str):
    """Extract first JSON object from LLM output (matches production client.py logic)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for m in re.finditer(r"[\{]", text):
        start = m.start()
        for end in range(len(text), start, -1):
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                continue
    return None


def validate_format(parsed) -> float:
    """Check JSON has required keys. Returns 1.0 (valid) or 0.0 (invalid)."""
    if not isinstance(parsed, dict):
        return 0.0
    if not REQUIRED_KEYS.issubset(parsed.keys()):
        return 0.0
    if not isinstance(parsed.get("options"), list) or len(parsed["options"]) != 4:
        return 0.0
    if parsed.get("correct") not in ("A", "B", "C", "D"):
        return 0.0
    return 1.0


# ---------------------------------------------------------------------------
# RAGAS evaluation with Gemini judge
# ---------------------------------------------------------------------------

def build_gemini_judge():
    """Build Google Gemini 2.5 Flash Lite wrapper for RAGAS evaluation."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("  ⚠ GOOGLE_API_KEY not set — RAGAS faithfulness/answer_relevancy will be None")
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from ragas.llms import LangchainLLMWrapper

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=api_key,
            temperature=0.0,
            max_retries=3,
        )

        # langchain-google-genai 1.0.x rejects `temperature` as a per-call kwarg,
        # but ragas 0.1.x passes it through. Drop it — temperature is set at init.
        class _GeminiJudge(LangchainLLMWrapper):
            def generate_text(self, prompt, n=1, temperature=None, stop=None, callbacks=None):
                result = self.langchain_llm.generate_prompt(
                    prompts=[prompt] * n, stop=stop, callbacks=callbacks,
                )
                if n > 1:
                    result.generations = [[g[0] for g in result.generations]]
                return result

            async def agenerate_text(self, prompt, n=1, temperature=None, stop=None, callbacks=None):
                result = await self.langchain_llm.agenerate_prompt(
                    prompts=[prompt] * n, stop=stop, callbacks=callbacks,
                )
                if n > 1:
                    result.generations = [[g[0] for g in result.generations]]
                return result

        return _GeminiJudge(llm)
    except Exception as e:
        print(f"  ⚠ Gemini judge setup failed: {e}")
        return None


def evaluate_with_ragas(rows: list, judge_llm) -> list[dict]:
    """Evaluate faithfulness for generated answers.

    Uses batched RAGAS evaluation with Gemini judge. Includes retry logic
    for rate limiting (HTTP 429).

    Returns list of {"faithfulness": float|None, "answer_relevancy": None}.

    NOTE: answer_relevancy was removed from the RAGAS metric set after
    Finding 4 showed it was a weak discriminator on MCQ-generation tasks.
    The column is still written (as None for new runs) for backward-compat
    with older CSVs. MCQ-side quality is now captured by the rubric metric
    (see benchmarks/rubric.py and Finding 5).
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
    from benchmarks import rubric

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
# Composite scoring
# ---------------------------------------------------------------------------

def composite_score(faithfulness, context_relevancy, mcq_quality, format_compliance):
    """Weighted composite v2: 0.4 faith + 0.3 ctx + 0.2 mcq_quality + 0.1 fmt.

    v1 formula (superseded — see Finding 4/5):
        0.4*faithfulness + 0.4*context_relevancy + 0.1*answer_relevancy + 0.1*format_compliance
    answer_relevancy was a weak discriminator on MCQ-generation (Finding 4);
    replaced by the task-specific rubric-based mcq_quality signal (Finding 5).
    ctx dropped from 0.4 to 0.3 to give the rubric 0.2; faithfulness kept at 0.4
    as the safety-critical anchor.
    """
    vals = [faithfulness, context_relevancy, mcq_quality, format_compliance]
    if any(v is None for v in vals):
        return None
    return round(
        (faithfulness * 0.4)
        + (context_relevancy * 0.3)
        + (mcq_quality * 0.2)
        + (format_compliance * 0.1),
        4,
    )


# ---------------------------------------------------------------------------
# CSV discovery
# ---------------------------------------------------------------------------

def find_latest_rag_csv(explicit_path: str | None = None) -> Path:
    """Find the most recent RAG benchmark results CSV."""
    if explicit_path:
        p = RESULTS_DIR / explicit_path if not Path(explicit_path).is_absolute() else Path(explicit_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Specified RAG CSV not found: {p}")

    csvs = sorted(RESULTS_DIR.glob("rag_*.csv"), reverse=True)
    if not csvs:
        raise FileNotFoundError(
            f"No RAG benchmark CSVs found in {RESULTS_DIR}.\n"
            "Run `python -m benchmarks.rag_benchmark` first."
        )
    return csvs[0]


def load_rag_results(csv_path: Path) -> list[dict]:
    """Load RAG retrieval results CSV."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows



# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_benchmarks(rag_csv_path: str | None = None, resume_csv: str | None = None):
    csv_path = find_latest_rag_csv(rag_csv_path)
    rag_rows = load_rag_results(csv_path)

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
    print("=" * 60)

    # Build Gemini judge
    judge_llm = build_gemini_judge()
    if judge_llm:
        print("RAGAS Judge : Google gemini-2.5-flash-lite ✓")
    else:
        print("RAGAS Judge : unavailable — faithfulness/answer_relevancy will be None")

    # Resume support: load existing results and detect completed models
    all_results = []
    completed_models = set()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if resume_csv:
        # Auto-detect latest partial CSV if no specific file given
        if resume_csv is True:
            csvs = sorted(RESULTS_DIR.glob("llm_*.csv"), reverse=True)
            resume_path = csvs[0] if csvs else None
        else:
            resume_path = RESULTS_DIR / resume_csv if not Path(resume_csv).is_absolute() else Path(resume_csv)

        if resume_path and resume_path.exists():
            all_results = load_rag_results(resume_path)
            completed_models = {r["generator_model"] for r in all_results}
            print(f"Resuming    : {resume_path.name} ({len(all_results)} rows, models done: {', '.join(sorted(completed_models))})")
            output_csv = resume_path
        else:
            print(f"No partial LLM CSV found — starting fresh")
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_csv = RESULTS_DIR / f"llm_{ts}.csv"
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_csv = RESULTS_DIR / f"llm_{ts}.csv"

    for model_idx, model in enumerate(GENERATOR_MODELS, 1):
        model_name = model["name"]
        model_tag = model["tag"]

        if model_name in completed_models:
            print(f"\n  [{model_idx}/{n_models}] Skipping {model_name} — already in resume CSV")
            continue

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

            row = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "generator_model": model_name,
                "emb_model": rag_row["emb_model"],
                "chunk_size": rag_row["chunk_size"],
                "chunk_overlap": rag_row["chunk_overlap"],
                "retrieval_type": rag_row["retrieval_type"],
                "question": rag_row["question"],
                "ground_truth": rag_row.get("ground_truth", ""),
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
                "context_relevancy": rag_row.get("context_relevancy"),
                "composite_score": None,
            }

            try:
                raw, latency = generate_question(model_tag, contexts)
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
            r["composite_score"] = composite_score(
                r["faithfulness"], ctx_rel, r["mcq_quality"], r["format_compliance"],
            )

        all_results.extend(model_rows)

        # Save incrementally after each model
        needs_header = not output_csv.exists() or output_csv.stat().st_size == 0
        with open(output_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if needs_header:
                writer.writeheader()
            for r in model_rows:
                write_row = {k: r.get(k) for k in CSV_FIELDS}
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
    parser.add_argument("--resume", nargs="?", const=True, default=None,
                        help="Resume from partial CSV (auto-detects latest, or specify filename)")
    args = parser.parse_args()

    run_benchmarks(args.rag_csv, resume_csv=args.resume)
