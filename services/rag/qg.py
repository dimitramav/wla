
# This file provides utilities for generating questions for a specific topic and document set.
#
# Key Features:
# - Defines templates for multiple-choice and yes/no questions.
# - Selects relevant text chunks based on keywords and embedding similarity.
# - Generates questions using an LLM (Large Language Model).

import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
from .vecstore import collection_for
from llm.prompts import SYSTEM_QG, USER_QG_MC_TEMPLATE, USER_QG_YN_TEMPLATE
from llm.client import generate_json, prompt_hash
from dataclasses import dataclass
from .settings import EMB_MODEL_ID
from chromadb.utils import embedding_functions
import numpy as np
import heapq

try:
    from rank_bm25 import BM25Okapi
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False

RETRIEVAL_LOG = Path(__file__).parent.parent / "retrieval_logs.jsonl"

# Configuration
MAX_CHARS_PER_Q = 450
POOL_PER_SOURCE = 30
POOL_MIN = 200
MAX_RETRIES = 2

emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMB_MODEL_ID
)

# QuestionTemplate class represents a question format.
@dataclass
class QuestionTemplate:
    kind: str
    template: str
    default_text: str
    default_correct: str
    options: List[str]
    
    def validate_response(self, text: str, correct: str) -> bool:
        if not text or len(text.strip()) < 10:
            return False
        if self.kind == "mcq":
            return correct in {"A", "B", "C", "D"}
        return True  # For yes/no questions

MCQ_TEMPLATE = QuestionTemplate(
    kind="mcq",
    template=USER_QG_MC_TEMPLATE,
    default_text="What is the main idea?",
    default_correct="B",
    options=["A) ...", "B) ...", "C) ...", "D) ..."]
)

YN_TEMPLATE = QuestionTemplate(
    kind="yesno",
    template=USER_QG_YN_TEMPLATE,
    default_text="Is the statement correct?",
    default_correct="Yes",
    options=["Yes", "No"]
)

def _ordered_chunks(col, topic: str, docset_hash: str) -> List[Tuple[str, Dict]]:
    """Returns (text, meta) pairs round-robin across sources.

    Each source contributes its chunks in (page, chunk_index) order; sources
    are cycled so every document in the docset is represented before any one
    document exhausts the pool budget. The pool budget scales with the number
    of sources (POOL_PER_SOURCE per doc, floored at POOL_MIN) so retrieval
    can reach the body of each document, not just the abstract/intro.
    """
    records = col.get(
        where={"$and": [{"topic": topic}, {"docset_hash": docset_hash}]},
        include=["documents", "metadatas"]
    )
    docs = records.get("documents", []) or []
    metas = records.get("metadatas", []) or []

    by_source: Dict[str, List[Tuple[str, Dict]]] = {}
    for txt, meta in zip(docs, metas):
        by_source.setdefault(meta.get("source", ""), []).append((txt, meta))

    for src in by_source:
        by_source[src].sort(key=lambda x: (
            x[1].get("page", 0),
            x[1].get("chunk_index", x[1].get("chunk_idx", 0))
        ))

    sources = sorted(by_source.keys())
    pool_budget = max(POOL_MIN, POOL_PER_SOURCE * len(sources))
    pool: List[Tuple[str, Dict]] = []
    idx = 0
    while len(pool) < pool_budget and any(idx < len(by_source[s]) for s in sources):
        for src in sources:
            if idx < len(by_source[src]):
                pool.append(by_source[src][idx])
                if len(pool) >= pool_budget:
                    break
        idx += 1
    return pool

# Trim text to a specified number of characters
def _trim(text: str, n: int = MAX_CHARS_PER_Q) -> str:
    """Trim text to n characters at word boundary"""
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + "…"

# Compute cosine similarity between two vectors
def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)


def _get_emb_fn(model: str = None):
    """Return embedding function for the given model, or the module-level default."""
    if model and model != EMB_MODEL_ID:
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
    return emb_fn


def _write_retrieval_log(
    topic: str,
    keyword_group: str,
    plan: List[Tuple[str, Dict, Optional[str]]],
    scores: List[float],
    retrieval_type: str,
) -> None:
    """Append a retrieval record line-by-line to retrieval_logs.jsonl."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "keyword_group": keyword_group,
        "retrieval_type": retrieval_type,
        "chunks": [
            {
                "chunk_id": f"{meta.get('source', '')}-c{meta.get('chunk_index', meta.get('chunk_idx', 0))}",
                "source": meta.get("source", ""),
                "score": scores[i] if i < len(scores) else None,
                "text_preview": txt[:120],
            }
            for i, (txt, meta, _) in enumerate(plan)
        ],
    }
    try:
        with RETRIEVAL_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # Non-critical: logging must not break question generation


def _pick_plan_by_keywords_hybrid(
    pool: List[Tuple[str, Dict]],
    keywords: List[str],
    needed: int,
    retrieval_type: str = "dense",
    _emb_fn=None,
    *,
    _chunk_vecs_cache: Optional[np.ndarray] = None,
    _kw_vecs_cache: Optional[Dict[str, np.ndarray]] = None,
) -> Tuple[List[Tuple[str, Dict, Optional[str]]], List[float]]:
    """Select chunks using dense-only or hybrid (dense + BM25 + RRF) retrieval.

    Dense path: ranks chunks by max cosine similarity across keywords.
    Hybrid path: merges dense ranks and BM25 sparse ranks via Reciprocal Rank Fusion
                 (Cormack et al., SIGIR 2009) using k=60.

    Returns (plan, scores) where plan is List[(text, meta, matched_kw)]
    and scores are the final relevance scores per chunk.
    """
    local_fn = _emb_fn or emb_fn

    if not keywords:
        return [(txt, meta, None) for txt, meta in pool[:needed]], [0.0] * min(needed, len(pool))

    chunk_texts = [txt for txt, _ in pool]
    n = len(chunk_texts)

    # --- Dense retrieval ---
    if _kw_vecs_cache is not None:
        kw_vecs = [_kw_vecs_cache[kw] for kw in keywords]
    else:
        kw_vecs = [local_fn(kw)[0] for kw in keywords]

    if _chunk_vecs_cache is not None:
        if len(_chunk_vecs_cache) != len(pool):
            raise ValueError(
                f"_chunk_vecs_cache length ({len(_chunk_vecs_cache)}) must equal len(pool) ({len(pool)})"
            )
        chunk_vecs = list(_chunk_vecs_cache)  # pre-computed, same order as pool
    else:
        chunk_vecs = [local_fn(txt)[0] for txt in chunk_texts]

    best_dense = np.zeros(n)
    best_kw = [None] * n
    for kw_idx, kw_vec in enumerate(kw_vecs):
        for ci, cv in enumerate(chunk_vecs):
            s = _cosine_similarity(np.array(kw_vec), np.array(cv))
            if s > best_dense[ci]:
                best_dense[ci] = s
                best_kw[ci] = keywords[kw_idx]

    dense_order = list(np.argsort(-best_dense))
    dense_rank = {int(i): r for r, i in enumerate(dense_order)}

    # --- Sparse retrieval: BM25 + RRF merge ---
    if retrieval_type == "hybrid" and _BM25_AVAILABLE and n > 0:
        try:
            tokenized = [t.lower().split() for t in chunk_texts]
            bm25 = BM25Okapi(tokenized)
            query_tokens = " ".join(keywords).lower().split()
            bm25_raw = bm25.get_scores(query_tokens)
            sparse_order = list(np.argsort(-bm25_raw))
            sparse_rank = {int(i): r for r, i in enumerate(sparse_order)}

            k = 60  # standard RRF constant (Cormack et al., 2009)
            final_scores = [
                1.0 / (k + dense_rank.get(i, n)) + 1.0 / (k + sparse_rank.get(i, n))
                for i in range(n)
            ]
        except Exception:
            final_scores = list(best_dense)
    else:
        final_scores = list(best_dense)

    final_order = sorted(range(n), key=lambda i: -final_scores[i])

    # Per-source cap: prevent any single document (typically its abstract)
    # from swallowing the plan. ceil(needed / num_sources_in_pool), floored at 1.
    sources_in_pool = {pool[i][1].get("source", "") for i in range(n)}
    max_per_source = max(1, -(-needed // max(1, len(sources_in_pool))))

    plan_with_scores, selected = [], set()
    per_source: Dict[str, int] = {}
    for ci in final_order:
        if len(plan_with_scores) >= needed:
            break
        if ci in selected:
            continue
        src = pool[ci][1].get("source", "")
        if per_source.get(src, 0) >= max_per_source:
            continue
        selected.add(ci)
        per_source[src] = per_source.get(src, 0) + 1
        txt, meta = pool[ci]
        # Always store cosine similarity as the score (not RRF) — RRF is
        # only used for ordering. This keeps scores comparable across retrieval types.
        plan_with_scores.append((txt, meta, best_kw[ci], float(best_dense[ci])))

    # Second pass: relax the cap if the capped pass left us short
    if len(plan_with_scores) < needed:
        for ci in final_order:
            if len(plan_with_scores) >= needed:
                break
            if ci in selected:
                continue
            selected.add(ci)
            txt, meta = pool[ci]
            plan_with_scores.append((txt, meta, best_kw[ci], float(best_dense[ci])))

    # Backfill if fewer chunks than needed
    for i, (txt, meta) in enumerate(pool):
        if len(plan_with_scores) >= needed:
            break
        if i not in selected:
            plan_with_scores.append((txt, meta, None, 0.0))
            selected.add(i)

    result = plan_with_scores[:needed]
    plan = [(txt, meta, kw) for txt, meta, kw, _ in result]
    scores = [s for _, _, _, s in result]
    return plan, scores

# Select chunks most similar to keywords
#
# Parameters:
# - pool: A list of text and metadata tuples.
# - keywords: A list of keywords to match.
# - needed: The number of chunks to select.
#
# Returns:
# - A list of tuples containing text, metadata, and matched keywords.
def _pick_plan_by_keywords(
    pool: List[Tuple[str, Dict]],
    keywords: List[str],
    needed: int,
) -> List[Tuple[str, Dict, Optional[str]]]:
    """Select chunks most semantically similar to keywords using embedding similarity."""
    if not keywords:
        return [(txt, meta, None) for txt, meta in pool[:needed]]

    # Step 1: Embed keywords
    kw_vecs = [emb_fn(kw)[0] for kw in keywords]  # returns list of vectors

    # Step 2: Embed chunks from the pool
    chunk_texts = [txt for txt, _ in pool]
    chunk_vecs = [emb_fn(txt)[0] for txt in chunk_texts]  # list of vectors

    # Step 3: Compute similarity and build plan
    heap = []  # Min-heap to keep top scoring (score, chunk_idx, keyword)

    for kw_idx, kw_vec in enumerate(kw_vecs):
        for chunk_idx, chunk_vec in enumerate(chunk_vecs):
            score = _cosine_similarity(np.array(kw_vec), np.array(chunk_vec))
            heapq.heappush(heap, (-score, chunk_idx, keywords[kw_idx]))  # negate for max-heap

    # Step 4: De-duplicate and select top N
    selected = set()
    plan = []

    while heap and len(plan) < needed:
        _, chunk_idx, matched_kw = heapq.heappop(heap)
        if chunk_idx in selected:
            continue
        selected.add(chunk_idx)
        txt, meta = pool[chunk_idx]
        plan.append((txt, meta, matched_kw))

    # Optional backfill if fewer than needed
    for i, (txt, meta) in enumerate(pool):
        if len(plan) >= needed:
            break
        if i not in selected:
            plan.append((txt, meta, None))
            selected.add(i)

    return plan[:needed]

# Generate a single question
def _generate_question(
    excerpt: str,
    seed: int,
    keyword: Optional[str],
    template: QuestionTemplate,
    dp: Optional[Dict] = None
) -> Dict:
    """Generate a single question with retries"""
    for attempt in range(MAX_RETRIES):
        user = template.template.format(
            excerpt=excerpt,
            context_span=dp.get("context_span", 1),
            distractor_strength=dp.get("distractor_strength", 1),
            application_share=int(dp.get("application_share", 0.0) * 100)
        )
        if keyword:
            user += f"\n\nGenerate a question specifically about the concept '{keyword}' based solely on the excerpt above."

        try:
            out = generate_json(SYSTEM_QG, user, seed=seed + attempt, temperature=0.3)
        except json.JSONDecodeError:
            continue

        if not isinstance(out, dict):
            continue

        text = out.get("text", "").strip()
        correct = str(out.get("correct", "")).strip().upper().replace(")", "")

        if template.validate_response(text, correct):
            return {
                "kind": template.kind,
                "text": text,
                "options": template.options if template.kind == "yesno" else out.get("options", template.options),
                "correct": "Yes" if template.kind == "yesno" and correct.lower().startswith("y") else
                          "No" if template.kind == "yesno" else correct,
                "why": out.get("why", "Grounded in the excerpt."),
                "evidence": str(out.get("evidence", "")).strip(),
            }

    # Default fallback
    return {
        "kind": template.kind,
        "text": template.default_text,
        "options": template.options,
        "correct": template.default_correct,
        "why": "Grounded in the excerpt.",
        "evidence": "",
    }

def _create_question_object(
    q: Dict,
    qid: str,
    keyword: Optional[str],
    meta: Dict,
    chunk_text: str = ""
) -> Dict:
    """Create standardized question object"""
    search_excerpt = re.sub(r'[#*>\[\]]', '', chunk_text).strip()
    return {
        "id": qid,
        "kind": q["kind"],
        "text": q["text"],
        "options": q["options"],
        "correct": q["correct"],
        "why": q["why"],
        "keywords": [keyword] if keyword else [],
        "source_spans": [{
            "doc": meta.get("source", ""),
            "text": search_excerpt,
        }]
    }

def _plan_split(
    pool: List[Tuple[str, Dict]],
    keywords: List[str],
    weak_keywords: Optional[List[str]],
    total_questions: int,
    weak_focus_ratio: float,
    retrieval_type: str,
    _fn,
    *,
    _chunk_vecs_cache: Optional[np.ndarray] = None,
    _kw_vecs_cache: Optional[Dict[str, np.ndarray]] = None,
    log_retrieval: bool = True,
    topic: str = "",
) -> Tuple[List[Tuple[str, Dict, Optional[str]]], List[float], List[Tuple[str, Dict, Optional[str]]], List[float]]:
    """Run the weak/strong retrieval split.

    Returns (weak_plan, weak_scores, strong_plan, strong_scores).
    The caches and log_retrieval kwargs are opt-in for the LLM-free
    simulation path (Phase 9 plan-only). Live callers pass nothing and
    get the original behaviour.
    """
    weak_focus_questions = int(total_questions * weak_focus_ratio)
    normal_questions = total_questions - weak_focus_questions

    weak_plan, weak_scores = _pick_plan_by_keywords_hybrid(
        pool, weak_keywords or [], weak_focus_questions, retrieval_type, _fn,
        _chunk_vecs_cache=_chunk_vecs_cache, _kw_vecs_cache=_kw_vecs_cache,
    )
    if log_retrieval:
        _write_retrieval_log(topic, "weak_keywords", weak_plan, weak_scores, retrieval_type)

    strong_keywords = list(set(keywords) - set(weak_keywords or []))
    strong_plan, strong_scores = _pick_plan_by_keywords_hybrid(
        pool, strong_keywords, normal_questions, retrieval_type, _fn,
        _chunk_vecs_cache=_chunk_vecs_cache, _kw_vecs_cache=_kw_vecs_cache,
    )
    if log_retrieval:
        _write_retrieval_log(topic, "strong_keywords", strong_plan, strong_scores, retrieval_type)

    return weak_plan, weak_scores, strong_plan, strong_scores


def plan_only(
    topic: str,
    docset_hash: str,
    mix: Dict,
    keywords: List[str],
    weak_keywords: Optional[List[str]],
    weak_focus_ratio: float = 0.65,
    retrieval_type: str = "dense",
    emb_model: str = None,
    *,
    _chunk_vecs_cache: Optional[np.ndarray] = None,
    _kw_vecs_cache: Optional[Dict[str, np.ndarray]] = None,
    _pool_cache: Optional[List[Tuple[str, Dict]]] = None,
) -> Dict:
    """LLM-free scheduler path. Returns targeted keywords without calling Ollama.

    Mirrors generate_qg's weak/strong split and per-question keyword assignment,
    but stops before _generate_question. Used by the Phase 9 simulation harness.
    Does NOT write to services/retrieval_logs.jsonl.
    """
    _fn = _get_emb_fn(emb_model)
    if _pool_cache is not None:
        pool = _pool_cache
    else:
        col = collection_for(topic, emb_model)
        pool = _ordered_chunks(col, topic, docset_hash)
    if not pool:
        return {"targeted_keywords": [], "weak_targets": [], "strong_targets": [],
                "weak_slot_n": 0, "strong_slot_n": 0}

    total_questions = int(mix.get("mcq", 0)) + int(mix.get("yesno", 0))

    weak_plan, _, strong_plan, _ = _plan_split(
        pool=pool,
        keywords=keywords,
        weak_keywords=weak_keywords,
        total_questions=total_questions,
        weak_focus_ratio=weak_focus_ratio,
        retrieval_type=retrieval_type,
        _fn=_fn,
        _chunk_vecs_cache=_chunk_vecs_cache,
        _kw_vecs_cache=_kw_vecs_cache,
        log_retrieval=False,
        topic=topic,
    )

    plan = weak_plan + strong_plan
    weak_slot_n = len(weak_plan)
    strong_slot_n = len(strong_plan)

    # Replicate the fallback assignment rule from generate_qg:451,461:
    # assigned_kw = matched_kw or (keywords[i % len(keywords)] if keywords else None)
    targeted = []
    for i, (_, _, matched_kw) in enumerate(plan):
        assigned = matched_kw or (keywords[i % len(keywords)] if keywords else None)
        targeted.append(assigned)

    weak_targets = targeted[:weak_slot_n]
    strong_targets = targeted[weak_slot_n:]

    return {
        "targeted_keywords": targeted,
        "weak_targets": weak_targets,
        "strong_targets": strong_targets,
        "weak_slot_n": weak_slot_n,
        "strong_slot_n": strong_slot_n,
    }


# Generate questions for a topic
def generate_qg(
    topic: str,
    docset_hash: str,
    mix: Dict,
    seed: str,  # Changed type hint to str
    keywords: List[str],
    weak_keywords: Optional[List[str]],
    weak_focus_ratio: float = 0.65,
    difficulty_profile: Dict = {},
    retrieval_type: str = "dense",
    emb_model: str = None,
) -> Dict:
    """Generate questions for a topic"""
    print(f"Generating QG for topic={topic} hash={docset_hash} with weak keywords={weak_keywords} and mix={mix}")
    # Convert seed string to integer using hash
    seed_int = hash(seed)

    _fn = _get_emb_fn(emb_model)
    col = collection_for(topic, emb_model)
    pool = _ordered_chunks(col, topic, docset_hash)
    if not pool:
        return {"questions": [], "promptHash": ""}

    mcq_n = int(mix.get("mcq", 10))
    yn_n = int(mix.get("yesno", 5))
    questions = []

    # Split questions between weak and normal keywords
    total_questions = mcq_n + yn_n

    weak_plan, weak_scores, strong_plan, strong_scores = _plan_split(
        pool=pool,
        keywords=keywords,
        weak_keywords=weak_keywords,
        total_questions=total_questions,
        weak_focus_ratio=weak_focus_ratio,
        retrieval_type=retrieval_type,
        _fn=_fn,
        log_retrieval=True,
        topic=topic,
    )

    # Combine plans
    plan = weak_plan + strong_plan
    
    # MCQs
    for i in range(min(mcq_n, len(plan))):
        text, meta, matched_kw = plan[i]
        excerpt = _trim(text)
        assigned_kw = matched_kw or (keywords[i % len(keywords)] if keywords else None)
        
        q = _generate_question(excerpt, seed_int + i, assigned_kw, MCQ_TEMPLATE, difficulty_profile)
        qid = f"q-{topic}-{docset_hash[:6]}-mcq-{i+1}"
        questions.append(_create_question_object(q, qid, assigned_kw, meta, text))

    # Yes/No
    for j in range(min(yn_n, max(0, len(plan) - mcq_n))):
        text, meta, matched_kw = plan[mcq_n + j]
        excerpt = _trim(text)
        assigned_kw = matched_kw or (keywords[(mcq_n + j) % len(keywords)] if keywords else None)
        
        q = _generate_question(excerpt, seed_int + 100 + j, assigned_kw, YN_TEMPLATE, difficulty_profile)
        qid = f"q-{topic}-{docset_hash[:6]}-yn-{j+1}"
        questions.append(_create_question_object(q, qid, assigned_kw, meta, text))

    demo_user = "\n\n".join(_trim(p[0], 200) for p in pool[:8])
    return {
        "questions": questions,
        "promptHash": prompt_hash(demo_user)
    }
