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

Requirements:
  - All services/requirements.txt dependencies installed in the active venv
  - Ollama running at http://localhost:11434 for RAGAS LLM evaluation
    (if Ollama is not running, context_relevancy scores are recorded as None)
"""

import csv
import sys
from pathlib import Path
from datetime import datetime, timezone

# Allow direct imports from the services/ package
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.golden_questions import GOLDEN_QUESTIONS

# ---------------------------------------------------------------------------
# Benchmark configuration matrix
# ---------------------------------------------------------------------------
EMBEDDING_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",   # baseline
    "sentence-transformers/all-mpnet-base-v2",
    "BAAI/bge-small-en-v1.5",
]

CHUNK_CONFIGS = [
    (512, 50),
    (800, 100),
]

RETRIEVAL_TYPES = ["dense", "hybrid"]

TOPIC = "school_anxiety"
RESULTS_DIR = Path(__file__).parent / "results"

CSV_FIELDS = [
    "timestamp",
    "emb_model",
    "chunk_size",
    "chunk_overlap",
    "retrieval_type",
    "question",
    "ground_truth",
    "keywords_used",
    "num_contexts",
    "contexts_text",
    "top_score",
    "context_relevancy",
]


# ---------------------------------------------------------------------------
# RAGAS evaluation
# ---------------------------------------------------------------------------

def _build_ragas_llm():
    """Try to build a LangChain Ollama wrapper for RAGAS. Returns None on failure."""
    try:
        from langchain_community.chat_models import ChatOllama
        from ragas.llms import LangchainLLMWrapper
        llm = ChatOllama(
            model="mistral:7b-instruct-q4_0",
            base_url="http://localhost:11434",
            timeout=300,
        )
        return LangchainLLMWrapper(llm)
    except Exception as e:
        print(f"  [RAGAS LLM setup failed: {e}]")
        return None


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
        run_cfg = RunConfig(max_workers=1, timeout=300)

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

def run_benchmarks():
    from rag.ingest import ingest_topic
    from rag.vecstore import collection_for
    from rag.qg import _ordered_chunks, _pick_plan_by_keywords_hybrid, _get_emb_fn

    print("=" * 60)
    print("WLA RAG Retrieval Benchmarking Suite")
    print(f"Topic       : {TOPIC}")
    print(f"Questions   : {len(GOLDEN_QUESTIONS)} (manually curated, corpus-grounded)")
    print(f"Configs     : {len(EMBEDDING_MODELS)} models x {len(CHUNK_CONFIGS)} chunk sizes x {len(RETRIEVAL_TYPES)} retrieval types")
    print(f"Total rows  : {len(GOLDEN_QUESTIONS) * len(EMBEDDING_MODELS) * len(CHUNK_CONFIGS) * len(RETRIEVAL_TYPES)}")
    print("=" * 60)

    ragas_llm = _build_ragas_llm()
    if ragas_llm:
        print("RAGAS: Ollama configured (mistral:7b-instruct-q4_0)")
    else:
        print("RAGAS: Ollama unavailable — context_relevancy will be None")

    results = []
    total_configs = len(EMBEDDING_MODELS) * len(CHUNK_CONFIGS) * len(RETRIEVAL_TYPES)
    config_num = 0

    for emb_model in EMBEDDING_MODELS:
        model_label = emb_model.split("/")[-1]

        for chunk_size, chunk_overlap in CHUNK_CONFIGS:
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
                continue

            col = collection_for(TOPIC, emb_model)
            _fn = _get_emb_fn(emb_model)
            pool = _ordered_chunks(col, TOPIC, docset_hash)

            if not pool:
                print("  No chunks found in collection — skipping")
                continue

            for retrieval_type in RETRIEVAL_TYPES:
                config_num += 1
                config_id = f"{model_label}_{chunk_size}_{chunk_overlap}_{retrieval_type}"
                print(f"\n  [{config_num}/{total_configs}] retrieval={retrieval_type}")

                # --- Retrieve for all questions first ---
                batch_questions, batch_contexts, batch_ground_truths = [], [], []
                batch_rows = []

                for item in GOLDEN_QUESTIONS:
                    question = item["question"]
                    ground_truth = item["ground_truth"]
                    keywords = item["keywords"]

                    try:
                        plan, scores = _pick_plan_by_keywords_hybrid(
                            pool,
                            keywords,
                            needed=5,
                            retrieval_type=retrieval_type,
                            _emb_fn=_fn,
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
                    print(f"    ✓ [{i+1}/10] score={row['top_score']}  ragas={row['context_relevancy']}")

                results.extend(batch_rows)

    # Write CSV with timestamped filename
    print(f"\n{'=' * 60}")
    if results:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_csv = RESULTS_DIR / f"rag_{ts}.csv"
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results written to {output_csv}  ({len(results)} rows)")
    else:
        print("No results to write — check ingestion errors above.")

    return results


if __name__ == "__main__":
    run_benchmarks()
