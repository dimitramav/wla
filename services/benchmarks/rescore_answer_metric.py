#!/usr/bin/env python3
"""
Offline re-scoring tool used to investigate the answer_relevancy cluster.

Investigation summary (see LLM_BENCHMARK_REPORT.md Finding 4):
  The original benchmark clustered every generator at 0.35-0.38 on RAGAS
  answer_relevancy. The initial hypothesis was a payload-shape artefact —
  RAGAS reverse-engineers questions from the "answer" text, so serialising the
  WLA answer as a full MCQ was suspected of dragging the metric. This script
  reparses `raw_output`, replaces the MCQ payload with just the grounded `why`
  explanation, and re-runs RAGAS against the frozen retrieval contexts.

  Result: with the production embedding (all-MiniLM-L6-v2), the payload change
  moves answer_relevancy by <=0.03 per generator — the hypothesis is NOT
  supported, and llm_benchmark.py was reverted to the original MCQ payload.
  The large +0.27 lift observed under Gemini embeddings is an embedding-model
  effect, not a payload effect.

  Both rescored CSVs are preserved as audit evidence:
    - llm_20260410_191454_rescored.csv         (Gemini embeddings, sensitivity)
    - llm_20260410_191454_rescored_minilm.csv  (MiniLM, production parity)

  This script is kept for future investigations that may need the same
  rig: frozen raw_output + frozen retrieval contexts + configurable RAGAS
  answer payload + swappable embedding model.

Usage:
  cd services && python -m benchmarks.rescore_answer_metric \\
      --llm-csv results/llm_20260410_191454.csv \\
      --rag-csv results/rag_20260410_160216.csv
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from benchmarks.llm_benchmark import extract_json  # reuse production parser

RESULTS_DIR = Path(__file__).parent / "results"


def build_gemini_stack():
    """Build Gemini judge LLM + local MiniLM embedding wrappers for RAGAS.

    Matches the embedding model used by llm_ragas_score.py and validated as the
    best-performing embedding for this corpus in the RAG retrieval benchmark
    (800/100 hybrid, RAGAS 0.867). Using it here gives the rescore parity with
    the production scoring path.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set")

    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=api_key,
        temperature=0.0,
        max_retries=3,
    )
    emb = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    )

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

    return _GeminiJudge(llm), emb


def extract_why_answer(raw_output: str) -> str:
    """Reparse raw_output and return a grounded explanation-only answer.

    Falls back to the correct-option text if `why` is empty, and to an empty
    string if the output cannot be parsed at all.
    """
    parsed = extract_json(raw_output or "")
    if not isinstance(parsed, dict):
        return ""
    why = (parsed.get("why") or "").strip()
    options = parsed.get("options") or []
    correct = parsed.get("correct") or ""
    correct_text = ""
    for opt in options:
        if isinstance(opt, str) and opt.startswith(f"{correct})"):
            correct_text = opt.split(")", 1)[1].strip()
            break
    if why and correct_text:
        return f"{correct_text}. {why}"
    return why or correct_text


def load_context_lookup(rag_csv: Path) -> dict:
    """Index rag CSV by (emb_model, chunk_size, chunk_overlap, retrieval_type, question)."""
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


def rescore(llm_csv: Path, rag_csv: Path, out_csv: Path, limit: int | None = None):
    ctx_lookup = load_context_lookup(rag_csv)

    with open(llm_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Build RAGAS dataset rows
    ragas_rows = []
    for r in rows:
        key = (
            r["emb_model"],
            r["chunk_size"],
            r["chunk_overlap"],
            r["retrieval_type"],
            r["question"],
        )
        contexts = ctx_lookup.get(key, [])
        answer_v2 = extract_why_answer(r.get("raw_output", ""))
        ragas_rows.append({
            "question": r["question"],
            "contexts": contexts,
            "answer": answer_v2,
            "ground_truth": r.get("ground_truth", ""),
            "_original_row": r,
            "_answer_v2": answer_v2,
        })

    valid = [x for x in ragas_rows if x["answer"] and x["contexts"] and x["ground_truth"]]
    if limit:
        valid = valid[:limit]
    print(f"Loaded {len(rows)} llm rows, {len(valid)} scorable after reparse/join" + (f" (limited)" if limit else ""))

    judge_llm, judge_emb = build_gemini_stack()

    from datasets import Dataset
    from ragas import evaluate as ragas_evaluate
    from ragas.metrics import answer_correctness, answer_relevancy
    from ragas.run_config import RunConfig

    answer_relevancy.llm = judge_llm
    answer_relevancy.embeddings = judge_emb
    answer_correctness.llm = judge_llm
    answer_correctness.embeddings = judge_emb

    run_cfg = RunConfig(max_workers=4, timeout=240)

    dataset = Dataset.from_dict({
        "question": [x["question"] for x in valid],
        "contexts": [x["contexts"] for x in valid],
        "answer": [x["answer"] for x in valid],
        "ground_truth": [x["ground_truth"] for x in valid],
    })

    max_attempts = 3
    df = None
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Running RAGAS (attempt {attempt}/{max_attempts})...")
            t0 = time.time()
            result = ragas_evaluate(
                dataset,
                metrics=[answer_relevancy, answer_correctness],
                run_config=run_cfg,
            )
            df = result.to_pandas()
            print(f"  done in {time.time() - t0:.1f}s")
            break
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < max_attempts:
                wait = 30 * attempt
                print(f"  rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            raise

    scored = {}
    for i, x in enumerate(valid):
        scored[id(x["_original_row"])] = {
            "answer_relevancy_v2": float(df["answer_relevancy"].iloc[i]),
            "answer_correctness": float(df["answer_correctness"].iloc[i]),
        }

    out_fields = list(rows[0].keys()) + ["answer_v2", "answer_relevancy_v2", "answer_correctness"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        for r, rag_row in zip(rows, ragas_rows):
            out = dict(r)
            out["answer_v2"] = rag_row["_answer_v2"]
            s = scored.get(id(r), {})
            out["answer_relevancy_v2"] = s.get("answer_relevancy_v2")
            out["answer_correctness"] = s.get("answer_correctness")
            writer.writerow(out)
    print(f"\nWrote {out_csv}  ({len(rows)} rows, {len(valid)} rescored)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rescore LLM CSV with fixed answer-side RAGAS metrics")
    parser.add_argument("--llm-csv", required=True, help="Path to existing llm_*.csv (relative to results/ or absolute)")
    parser.add_argument("--rag-csv", required=True, help="Path to the frozen rag_*.csv used during generation")
    parser.add_argument("--out-csv", help="Output CSV path (default: <llm-csv stem>_rescored.csv)")
    parser.add_argument("--limit", type=int, help="Smoke-test: only score first N valid rows")
    args = parser.parse_args()

    def _resolve(p: str) -> Path:
        pp = Path(p)
        if pp.is_absolute() or pp.exists():
            return pp
        return RESULTS_DIR / pp.name

    llm_path = _resolve(args.llm_csv)
    rag_path = _resolve(args.rag_csv)
    out_path = _resolve(args.out_csv) if args.out_csv else llm_path.with_name(llm_path.stem + "_rescored.csv")

    rescore(llm_path, rag_path, out_path, limit=args.limit)
