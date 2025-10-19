
# This file provides utilities for generating questions for a specific topic and document set.
#
# Key Features:
# - Defines templates for multiple-choice and yes/no questions.
# - Selects relevant text chunks based on keywords and embedding similarity.
# - Generates questions using an LLM (Large Language Model).

from typing import List, Dict, Tuple, Optional
from .vecstore import collection_for
from llm.prompts import SYSTEM_QG, USER_QG_MC_TEMPLATE, USER_QG_YN_TEMPLATE
from llm.client import generate_json, prompt_hash
from dataclasses import dataclass
from .settings import  EMB_MODEL_ID
from chromadb.utils import embedding_functions
import numpy as np
import heapq

# Configuration
MAX_CHARS_PER_Q = 450
POOL_TOP = 24
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
    """Returns stably-ordered list of (text, meta) filtered by topic+hash"""
    records = col.get(
        where={"$and": [{"topic": topic}, {"docset_hash": docset_hash}]},
        include=["documents", "metadatas"]
    )
    docs = records.get("documents", []) or []
    metas = records.get("metadatas", []) or []
    pairs = list(zip(docs, metas))
    pairs.sort(key=lambda x: (
        x[1].get("source", ""),
        x[1].get("page", 0),
        x[1].get("chunk_idx", 0)
    ))
    return pairs[:POOL_TOP]

# Trim text to a specified number of characters
def _trim(text: str, n: int = MAX_CHARS_PER_Q) -> str:
    """Trim text to n characters at word boundary"""
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + "…"

# Compute cosine similarity between two vectors
def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

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

        out = generate_json(SYSTEM_QG, user, seed=seed + attempt, temperature=0.3)

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
                "why": out.get("why", "Grounded in the excerpt.")
            }

    # Default fallback
    return {
        "kind": template.kind,
        "text": template.default_text,
        "options": template.options,
        "correct": template.default_correct,
        "why": "Grounded in the excerpt."
    }

def _create_question_object(
    q: Dict,
    qid: str,
    keyword: Optional[str],
    meta: Dict
) -> Dict:
    """Create standardized question object"""
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
            "page_from": meta.get("page", 0),
            "page_to": meta.get("page", 0),
            "chunk_id": f"{meta.get('source', '')}-p{meta.get('page', 0)}-c{meta.get('chunk_idx', 0)}"
        }]
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
    difficulty_profile: Dict = {}
) -> Dict:
    """Generate questions for a topic"""
    print(f"Generating QG for topic={topic} hash={docset_hash} with weak keywords={weak_keywords} and mix={mix}")
    # Convert seed string to integer using hash
    seed_int = hash(seed)
    
    col = collection_for(topic)
    pool = _ordered_chunks(col, topic, docset_hash)
    if not pool:
        return {"questions": [], "promptHash": ""}

    mcq_n = int(mix.get("mcq", 10))
    yn_n = int(mix.get("yesno", 5))
    questions = []

    # Generate all questions
    # Split questions between weak and normal keywords
    total_questions = mcq_n + yn_n
    weak_focus_questions = int(total_questions * weak_focus_ratio)
    normal_questions = total_questions - weak_focus_questions
    
    # Get plans for both weak and strong keywords
    weak_plan = _pick_plan_by_keywords(pool, weak_keywords or [], weak_focus_questions)
    strong_keywords = list(set(keywords) - set(weak_keywords or []))
    strong_plan = _pick_plan_by_keywords(pool, strong_keywords, normal_questions)

    # Combine plans
    plan = weak_plan + strong_plan
    
    # MCQs
    for i in range(min(mcq_n, len(plan))):
        text, meta, matched_kw = plan[i]
        excerpt = _trim(text)
        assigned_kw = matched_kw or (keywords[i % len(keywords)] if keywords else None)
        
        q = _generate_question(excerpt, seed_int + i, assigned_kw, MCQ_TEMPLATE, difficulty_profile)
        qid = f"q-{topic}-{docset_hash[:6]}-mcq-{i+1}"
        questions.append(_create_question_object(q, qid, assigned_kw, meta))

    # Yes/No
    for j in range(min(yn_n, max(0, len(plan) - mcq_n))):
        text, meta, matched_kw = plan[mcq_n + j]
        excerpt = _trim(text)
        assigned_kw = matched_kw or (keywords[(mcq_n + j) % len(keywords)] if keywords else None)
        
        q = _generate_question(excerpt, seed_int + 100 + j, assigned_kw, YN_TEMPLATE, difficulty_profile)
        qid = f"q-{topic}-{docset_hash[:6]}-yn-{j+1}"
        questions.append(_create_question_object(q, qid, assigned_kw, meta))

    demo_user = "\n\n".join(_trim(p[0], 200) for p in pool[:8])
    return {
        "questions": questions,
        "promptHash": prompt_hash(demo_user)
    }
