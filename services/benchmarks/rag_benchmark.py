#!/usr/bin/env python3
"""
RAG retrieval benchmarking script for Watch-Listen-Act.

Tests all combinations of embedding model x chunking strategy x retrieval type
against a manually curated golden question set grounded in the corpus documents.

What this evaluates:
  For each question, we ask ChromaDB to retrieve relevant chunks.
  RAGAS then judges whether those chunks actually contain the knowledge
  needed to generate a good quiz question about that concept.
  This tells you which config produces the most relevant chunk retrieval —
  which directly affects quiz question quality for teacher training.

Outputs:
  services/benchmarks/results/rag_YYYYMMDD_HHMMSS.csv — one row per question per configuration
  services/retrieval_logs.jsonl              — per-query chunk retrieval trace (appended)

Usage:
  cd services && python -m benchmarks.rag_benchmark
  cd services && python -m benchmarks.rag_benchmark --resume 5

Requirements:
  - All services/requirements.txt dependencies installed in the active venv
  - Ollama running at http://localhost:11434 for RAGAS LLM evaluation
    (if Ollama is not running, context_relevancy scores are recorded as None)
"""

import argparse
import csv
import requests
import sys
from pathlib import Path
from datetime import datetime, timezone

# Allow direct imports from the services/ package
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import numpy as np

from benchmarks.config import (
    CHUNK_CONFIGS,
    EMBEDDING_MODELS,
    RAG_CSV_FIELDS,
    RETRIEVAL_TYPES,
    TOPIC,
)
from benchmarks.fixtures import GOLDEN_QUESTIONS
from benchmarks.io import RESULTS_DIR
from benchmarks.scoring.judge import build_gemini_judge, build_ollama_judge


# ---------------------------------------------------------------------------
# RAGAS evaluation
# ---------------------------------------------------------------------------

def evaluate_batch_with_ragas(
    questions: list,
    contexts_list: list,
    ground_truths: list,
    ragas_llm=None,
) -> list:
    """Score a batch of retrieved context sets with RAGAS context_precision.

    Batches all questions for a config into a single Ollama call instead of
    one call per question — ~10x faster than individual evaluation.

    Returns list of {"context_relevancy": float | None}, one per question.
    """
    n = len(questions)
    try:
        from datasets import Dataset
        from ragas import evaluate as ragas_evaluate
        from ragas.metrics import context_precision
        from ragas.run_config import RunConfig

        if ragas_llm is not None:
            context_precision.llm = ragas_llm

        # Ollama serves one request at a time — sequential evaluation
        # prevents 9/10 jobs timing out from concurrent queuing.
        # 600s timeout to accommodate CPU-only inference.
        run_cfg = RunConfig(max_workers=1, timeout=600)

        data = {
            "question": questions,
            "contexts": contexts_list,
            "answer": [""] * n,
            "ground_truth": ground_truths,  # singular, non-deprecated form
        }
        dataset = Dataset.from_dict(data)
        result = ragas_evaluate(dataset, metrics=[context_precision],
                                run_config=run_cfg)
        df = result.to_pandas()
        return [{"context_relevancy": float(v)} for v in df["context_precision"]]
    except Exception as e:
        print(f"  [RAGAS batch skipped: {type(e).__name__}: {e}]")
        return [{"context_relevancy": None}] * n


# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

def _keep_ollama_alive(model: str = "mistral:7b-instruct-q4_0"):
    """Tell Ollama to keep the model loaded for 24h to prevent unloading mid-run."""
    try:
        requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": "", "keep_alive": "24h"},
            timeout=120,
        )
        print(f"Ollama keep_alive set to 24h for {model}")
    except Exception as e:
        print(f"  ⚠ Could not set keep_alive: {e}")


def _append_rows_to_csv(output_csv: Path, rows: list, write_header: bool):
    """Append rows to the CSV file incrementally."""
    with open(output_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAG_CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def run_benchmarks(resume_from: int = 1):
    from rag.ingest import ingest_topic
    from rag.vecstore import collection_for
    from rag.qg import _ordered_chunks, _pick_plan_by_keywords_hybrid, _get_emb_fn

    total_configs = len(EMBEDDING_MODELS) * len(CHUNK_CONFIGS) * len(RETRIEVAL_TYPES)

    print("=" * 60)
    print("WLA RAG Retrieval Benchmarking Suite")
    print(f"Topic       : {TOPIC}")
    print(f"Questions   : {len(GOLDEN_QUESTIONS)} (manually curated, corpus-grounded)")
    print(f"Configs     : {len(EMBEDDING_MODELS)} models x {len(CHUNK_CONFIGS)} chunk sizes x {len(RETRIEVAL_TYPES)} retrieval types")
    print(f"Total rows  : {len(GOLDEN_QUESTIONS) * total_configs}")
    if resume_from > 1:
        print(f"Resuming    : from config {resume_from}/{total_configs}")
    print("=" * 60)

    ragas_llm = build_ollama_judge()
    if ragas_llm:
        print("RAGAS: Ollama configured (mistral:7b-instruct-q4_0)")
        _keep_ollama_alive()
    else:
        print("RAGAS: Ollama unavailable — context_relevancy will be None")

    # Incremental CSV — timestamped file, write header once
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_csv = RESULTS_DIR / f"rag_{ts}.csv"
    header_written = False

    # Build flat config list so numbering is always correct
    all_configs = []
    for emb_model in EMBEDDING_MODELS:
        for chunk_size, chunk_overlap in CHUNK_CONFIGS:
            for retrieval_type in RETRIEVAL_TYPES:
                all_configs.append((emb_model, chunk_size, chunk_overlap, retrieval_type))

    results = []
    prev_ingest_key = None
    col = _fn = pool = None

    for config_num, (emb_model, chunk_size, chunk_overlap, retrieval_type) in enumerate(all_configs, 1):
        model_label = emb_model.split("/")[-1]
        ingest_key = (emb_model, chunk_size, chunk_overlap)

        if config_num < resume_from:
            print(f"\n  [{config_num}/{total_configs}] retrieval={retrieval_type}  — SKIPPED (resume)")
            continue

        # Only re-ingest when model or chunk config changes
        if ingest_key != prev_ingest_key:
            print(f"\n{'─' * 60}")
            print(f"Ingesting: {model_label}  chunks={chunk_size}/{chunk_overlap}")

            try:
                ingest_result = ingest_topic(
                    TOPIC,
                    force=True,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    emb_model=emb_model,
                )
                docset_hash = ingest_result.get("docset_hash", "")
                print(f"  chunks_upserted={ingest_result.get('chunks_upserted', 0)}  hash={docset_hash[:8]}")
            except Exception as e:
                print(f"  Ingestion FAILED: {e}")
                prev_ingest_key = None
                continue

            col = collection_for(TOPIC, emb_model)
            _fn = _get_emb_fn(emb_model)
            pool = _ordered_chunks(col, TOPIC, docset_hash)

            if not pool:
                print("  No chunks found in collection — skipping")
                prev_ingest_key = None
                continue

            prev_ingest_key = ingest_key

            # Pre-compute chunk embeddings once per ingestion (reused across retrieval types + questions)
            print(f"  Pre-computing {len(pool)} chunk embeddings...")
            chunk_vecs = np.array([_fn(txt)[0] for txt, _ in pool])
            print(f"  ✓ Chunk embeddings cached")

            # Pre-compute keyword embeddings for all golden questions
            all_kws = set()
            for item in GOLDEN_QUESTIONS:
                all_kws.update(item["keywords"])
            kw_vecs_cache = {kw: _fn(kw)[0] for kw in all_kws}
            print(f"  ✓ {len(kw_vecs_cache)} keyword embeddings cached")

        if pool is None:
            continue

        config_id = f"{model_label}_{chunk_size}_{chunk_overlap}_{retrieval_type}"
        print(f"\n  [{config_num}/{total_configs}] retrieval={retrieval_type}")

        # --- Retrieve for all questions first ---
        batch_questions, batch_contexts, batch_ground_truths = [], [], []
        batch_rows = []

        for item in GOLDEN_QUESTIONS:
            question = item["question"]
            ground_truth = item["ground_truth"]
            keywords = item["keywords"]
            difficulty_label = item.get("difficulty_label", "")

            try:
                plan, scores = _pick_plan_by_keywords_hybrid(
                    pool,
                    keywords,
                    needed=5,
                    retrieval_type=retrieval_type,
                    _emb_fn=_fn,
                    _chunk_vecs_cache=chunk_vecs,
                    _kw_vecs_cache=kw_vecs_cache,
                )
                contexts = [txt for txt, _, _ in plan]
                top_score = round(max(scores), 4) if scores else None
            except Exception as e:
                print(f"    Retrieval ERROR: {e}")
                contexts, top_score = [], None

            batch_questions.append(question)
            batch_contexts.append(contexts)
            batch_ground_truths.append(ground_truth)
            batch_rows.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "emb_model": emb_model,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "retrieval_type": retrieval_type,
                "question": question,
                "ground_truth": ground_truth,
                "keywords_used": "|".join(keywords),
                "difficulty_label": difficulty_label,
                "num_contexts": len(contexts),
                "contexts_text": "|||".join(contexts),
                "top_score": top_score,
                "context_relevancy": None,
            })

        # --- RAGAS: one batch call per config ---
        print(f"    Running RAGAS batch ({len(batch_questions)} questions)...")
        ragas_batch = evaluate_batch_with_ragas(
            batch_questions, batch_contexts, batch_ground_truths, ragas_llm
        )
        for i, row in enumerate(batch_rows):
            row["context_relevancy"] = ragas_batch[i].get("context_relevancy")
            print(f"    ✓ [{i+1}/{len(GOLDEN_QUESTIONS)}] score={row['top_score']}  ragas={row['context_relevancy']}")

        # --- Save incrementally after each config ---
        _append_rows_to_csv(output_csv, batch_rows, write_header=not header_written)
        header_written = True
        print(f"    ✓ Config {config_num}/{total_configs} saved to {output_csv.name}")

        results.extend(batch_rows)

    print(f"\n{'=' * 60}")
    if results:
        print(f"Results written to {output_csv}  ({len(results)} rows)")
    else:
        print("No results to write — check ingestion errors above.")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG retrieval benchmark")
    parser.add_argument("--resume", type=int, default=1,
                        help="Config number to resume from (e.g. --resume 5 skips configs 1-4)")
    args = parser.parse_args()
    run_benchmarks(resume_from=args.resume)
