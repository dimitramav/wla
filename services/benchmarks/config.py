"""
Benchmark configuration matrix and CSV schemas.

Shared by the RAG retrieval benchmark, the LLM generation benchmark, and
the offline rescoring tools so the configuration surface stays in lock-step
across all pipelines.
"""

TOPIC = "school_anxiety"

# ---------------------------------------------------------------------------
# RAG retrieval matrix
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


# ---------------------------------------------------------------------------
# Generator models — all local Ollama, Q4_0 quantized.
#
# Pulled/removed sequentially during a benchmark run to keep disk usage
# bounded.
# ---------------------------------------------------------------------------
GENERATOR_MODELS = [
    {
        "name": "mistral-7b",
        "tag": "mistral:7b-instruct-q4_0",
        "pull_needed": True,
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


# ---------------------------------------------------------------------------
# CSV schemas
# ---------------------------------------------------------------------------
RAG_CSV_FIELDS = [
    "timestamp",
    "emb_model",
    "chunk_size",
    "chunk_overlap",
    "retrieval_type",
    "question",
    "ground_truth",
    "keywords_used",
    "difficulty_label",
    "num_contexts",
    "contexts_text",
    "top_score",
    "context_relevancy",
]

# `answer_relevancy` is retained for backward-compat with pre-Finding-5
# runs; it is no longer computed or used in the composite score.
LLM_CSV_FIELDS = [
    "timestamp",
    "generator_model",
    "emb_model",
    "chunk_size",
    "chunk_overlap",
    "retrieval_type",
    "question",
    "ground_truth",
    "difficulty_label",
    "format_compliance",
    "response_time_s",
    "raw_output",
    "generated_answer",
    "faithfulness",
    "answer_relevancy",
    "stem_clarity",
    "distractor_plausibility",
    "pedagogical_appropriateness",
    "mcq_quality",
    "text_independence",
    "context_relevancy",
    "composite_score",
]
