from typing import List, Dict, Tuple, Optional
from .vecstore import collection_for
from .settings import read_docsets_meta
from llm.prompts import SYSTEM_QG, USER_QG_MC_TEMPLATE, USER_QG_YN_TEMPLATE
from llm.client import generate_json, prompt_hash
from dataclasses import dataclass

# Configuration
MAX_CHARS_PER_Q = 450
POOL_TOP = 24
MAX_RETRIES = 2

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

def _trim(text: str, n: int = MAX_CHARS_PER_Q) -> str:
    """Trim text to n characters at word boundary"""
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + "…"

def _pick_plan_by_keywords(
    pool: List[Tuple[str, Dict]],
    keywords: List[str],
    needed: int
) -> List[Tuple[str, Dict, Optional[str]]]:
    """Select chunks based on keywords with backfill"""
    kws = {k.strip().lower() for k in keywords or [] if k.strip()}
    used = set()
    plan = []

    # Match keywords
    if kws:
        for idx, (txt, meta) in enumerate(pool):
            if len(plan) >= needed:
                break
            low = txt.lower()
            matched = next((k for k in kws if k in low), None)
            if matched:
                plan.append((txt, meta, matched))
                used.add(idx)

    # Backfill
    for idx, (txt, meta) in enumerate(pool):
        if len(plan) >= needed:
            break
        if idx not in used:
            plan.append((txt, meta, None))
            used.add(idx)

    return plan[:needed]

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
            user += f"\n\nFocus on concept: {keyword}"
            
        out = generate_json(SYSTEM_QG, user, seed=seed + attempt, temperature=0.0)
        
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

def generate_qg(
    topic: str,
    docset_hash: str,
    mix: Dict,
    seed: str,  # Changed type hint to str
    keywords: List[str],
    difficulty_profile: Dict = {}
) -> Dict:
    """Generate questions for a topic"""
    print(f"Generating QG for topic={topic} hash={docset_hash} with keywords={keywords} and mix={mix}")
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
    plan = _pick_plan_by_keywords(pool, keywords, mcq_n + yn_n)
    
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
