#!/usr/bin/env python3
"""
RAG pipeline benchmarking script for Watch-Listen-Act.

Tests all combinations of embedding model x chunking strategy x retrieval type
against a manually curated golden question set grounded in the corpus documents.

What this evaluates:
  For each question, we ask ChromaDB to retrieve relevant chunks.
  RAGAS then judges whether those chunks actually contain the knowledge
  needed to generate a good quiz question about that concept.
  This tells you which config produces the most relevant chunk retrieval —
  which directly affects quiz question quality for teacher training.

Outputs:
  services/benchmark_results.csv  — one row per question per configuration
  services/retrieval_logs.jsonl   — per-query chunk retrieval trace (appended)

Usage:
  cd services && python run_benchmarks.py

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
sys.path.insert(0, str(Path(__file__).parent))

# ---------------------------------------------------------------------------
# Golden question set
#
# Each question is:
#   - Grounded in specific content from the corpus documents
#   - Paired with the corpus source it comes from (for traceability)
#   - Paired with a ground truth drawn from that document's actual content
#   - Paired with retrieval keywords (matching the taxonomy in keywords.yaml)
#     that the system would use to find relevant chunks
#
# These questions are manually written — not AI-generated — to avoid the
# circularity of evaluating LLM retrieval with LLM-generated queries.
# ---------------------------------------------------------------------------
GOLDEN_QUESTIONS = [
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Ways 1 & 3)
        "question": "When a student expresses worry, should a teacher immediately reassure them that everything will be fine?",
        "ground_truth": "No. Teachers should first listen, empathise and validate the student's feelings. Early reassurance like 'everything is fine' can feel dismissive. Recognising feelings as normal comes before offering solutions.",
        "keywords": ["common signs and symptoms", "somatic complaints"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 2)
        "question": "Why is it important for teachers to appear calm when supporting an anxious student, even if the teacher feels anxious themselves?",
        "ground_truth": "Children watch the behaviour of adults around them to judge whether they too should feel anxious. A calm teacher signals that the situation is manageable, which helps reassure the student.",
        "keywords": ["common signs and symptoms", "social evaluation fears"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 4)
        "question": "How can a teacher help a student challenge an anxious thought about a feared situation?",
        "ground_truth": "By introducing alternative perspectives — reminding the student that a worry is a thought, not necessarily a fact, and exploring how likely the feared outcome really is and what it would mean if it did happen.",
        "keywords": ["cognitive restructuring"],
    },
    {
        # Source: annafreud_seven_ways_support_worried.pdf (Way 7)
        "question": "What is the Anxiety Thermometer and how is it used to monitor a student's progress?",
        "ground_truth": "The Anxiety Thermometer is a 0-to-10 scale based on the child's response: 0 is calm and content, 10 is extremely anxious. It is used to track whether interventions are reducing anxiety over time.",
        "keywords": ["response systems", "autonomic arousal"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (statistics)
        "question": "What does the research say about trends in persistent school absence in recent years?",
        "ground_truth": "Research from the Children's Commissioner found that persistent absence more than doubled: from 10.9% of all pupils in 2018/19 to 22.3% in 2022/23.",
        "keywords": ["attendance tracking", "somatic complaints"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (early indicators)
        "question": "What early physical and behavioural signs might indicate that a student's non-attendance is rooted in anxiety?",
        "ground_truth": "Physical signs linked to stress such as stomach ache, sickness or headache; a parent reporting the child does not want to come to school; and behavioural changes like reduced engagement with others and learning.",
        "keywords": ["somatic complaints", "attendance tracking", "common signs and symptoms"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (case study - graded exposure)
        "question": "Describe a graded exposure approach that can be used to support a student with anxiety-driven school non-attendance.",
        "ground_truth": "A stepladder approach creates a graded hierarchy of exposure to the feared situation. The student starts with smaller steps — such as meeting a friend from school or completing work at home — and gradually transitions to a safe space in school before rejoining peers in class.",
        "keywords": ["graduated exposure", "attendance tracking"],
    },
    {
        # Source: annafreud_school_attendance_mental_wellbeing.pdf (whole-school)
        "question": "What does a whole-school approach to mental health involve and why does it help with non-attendance?",
        "ground_truth": "It involves all aspects of the school community in promoting wellbeing, developing a culture that prioritises safety and support, and reducing the impact of non-attendance risk factors for pupils, staff and families.",
        "keywords": ["school social climate", "student–teacher relations", "parent-teacher collaboration"],
    },
    {
        # Source: johnson2023_teacher_mh_literacy_review.pdf
        "question": "According to the research, how does teacher recognition of anxiety compare to their recognition of ADHD in children?",
        "ground_truth": "Teachers appear to have good recognition of childhood ADHD, but their knowledge and recognition of internalising disorders such as anxiety is less clear. Little research has focused on these problems specifically.",
        "keywords": ["common signs and symptoms", "internalizing symptoms"],
    },
    {
        # Source: schlesier2023_bullying_anxiety_absenteeism.pdf
        "question": "How are school bullying, school anxiety and school absenteeism related to each other?",
        "ground_truth": "Research shows these three constructs are interconnected. Bullying victimisation can trigger school anxiety, and school anxiety in turn predicts absenteeism. Gender and grade level moderate these relationships in secondary school students.",
        "keywords": ["peer aggression", "social evaluation fears", "attendance tracking"],
    },
]

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
OUTPUT_CSV = Path(__file__).parent / "benchmark_results.csv"

CSV_FIELDS = [
    "timestamp",
    "emb_model",
    "chunk_size",
    "chunk_overlap",
    "retrieval_type",
    "question",
    "keywords_used",
    "contexts_retrieved",
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
    print("WLA RAG Benchmarking Suite")
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
                        "keywords_used": "|".join(keywords),
                        "contexts_retrieved": len(contexts),
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

    # Write CSV
    print(f"\n{'=' * 60}")
    if results:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results written to {OUTPUT_CSV}  ({len(results)} rows)")
    else:
        print("No results to write — check ingestion errors above.")

    return results


if __name__ == "__main__":
    run_benchmarks()
