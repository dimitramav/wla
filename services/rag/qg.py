from typing import List, Dict, Tuple, Optional
from .vecstore import collection_for
from .settings import read_docsets_meta
from llm.prompts import SYSTEM_QG, USER_QG_MC_TEMPLATE, USER_QG_YN_TEMPLATE
from llm.client import generate_json, prompt_hash
from dataclasses import dataclass

# Configuration
MAX_CHARS_PER_Q = 450
POOL_TOP = 24
MAX_RETRIES = 3

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

def _generate_batch_questions(
    excerpts: List[str],
    seed: int,
    keywords: List[Optional[str]],
    template: QuestionTemplate,
    dp: Optional[Dict] = None
) -> List[Dict]:
    """Generate multiple questions in one LLM call"""
    # Combine all excerpts and keywords into one prompt
    prompts = []
    for i, (excerpt, keyword) in enumerate(zip(excerpts, keywords)):
        prompt = template.template.format(
            excerpt=excerpt,
            context_span=dp.get("context_span", 1),
            distractor_strength=dp.get("distractor_strength", 1),
            application_share=int(dp.get("application_share", 0.0) * 100)
        )
        if keyword:
            prompt += f"\n\nFocus on concept: {keyword}"
        prompts.append(f"Question {i+1}:\n{prompt}")
    
    combined_prompt = "\n\n---\n\n".join(prompts)
    
    # Single LLM call for all questions
    out = generate_json(SYSTEM_QG, combined_prompt, seed=seed, temperature=0.0)
    
    if not isinstance(out, dict) or "questions" not in out:
        # Fallback: return defaults for all questions
        return [{
            "kind": template.kind,
            "text": template.default_text,
            "options": template.options,
            "correct": template.default_correct,
            "why": "Grounded in the excerpt."
        } for _ in excerpts]
    
    results = []
    for q in out.get("questions", []):
        text = q.get("text", "").strip()
        correct = str(q.get("correct", "")).strip().upper().replace(")", "")
        
        if template.validate_response(text, correct):
            results.append({
                "kind": template.kind,
                "text": text,
                "options": template.options if template.kind == "yesno" else q.get("options", template.options),
                "correct": "Yes" if template.kind == "yesno" and correct.lower().startswith("y") else 
                          "No" if template.kind == "yesno" else correct,
                "why": q.get("why", "Grounded in the excerpt.")
            })
        else:
            results.append({
                "kind": template.kind,
                "text": template.default_text,
                "options": template.options,
                "correct": template.default_correct,
                "why": "Grounded in the excerpt."
            })
            
    # Ensure we return same number of questions as inputs
    while len(results) < len(excerpts):
        results.append({
            "kind": template.kind,
            "text": template.default_text,
            "options": template.options,
            "correct": template.default_correct,
            "why": "Grounded in the excerpt."
        })
        
    return results

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
    seed: int,
    keywords: List[str],
    difficulty_profile: Dict = {}
) -> Dict:
    """Generate questions for a topic"""
    col = collection_for(topic)
    pool = _ordered_chunks(col, topic, docset_hash)
    if not pool:
        return {"questions": [], "promptHash": ""}

    mcq_n = int(mix.get("mcq", 10))
    yn_n = int(mix.get("yesno", 5))
    questions = []

    # Generate all questions
    plan = _pick_plan_by_keywords(pool, keywords, mcq_n + yn_n)
    
    # Prepare MCQ batch
    mcq_excerpts = []
    mcq_keywords = []
    mcq_meta = []
    for i in range(min(mcq_n, len(plan))):
        text, meta, matched_kw = plan[i]
        mcq_excerpts.append(_trim(text))
        assigned_kw = matched_kw or (keywords[i % len(keywords)] if keywords else None)
        mcq_keywords.append(assigned_kw)
        mcq_meta.append(meta)

    # Generate all MCQs in one call
    if mcq_excerpts:
        mcq_results = _generate_batch_questions(mcq_excerpts, seed, mcq_keywords, MCQ_TEMPLATE, difficulty_profile)
        for i, (q, kw, meta) in enumerate(zip(mcq_results, mcq_keywords, mcq_meta)):
            qid = f"q-{topic}-{docset_hash[:6]}-mcq-{i+1}"
            questions.append(_create_question_object(q, qid, kw, meta))

    # Prepare YN batch
    yn_excerpts = []
    yn_keywords = []
    yn_meta = []
    for j in range(min(yn_n, max(0, len(plan) - mcq_n))):
        text, meta, matched_kw = plan[mcq_n + j]
        yn_excerpts.append(_trim(text))
        assigned_kw = matched_kw or (keywords[(mcq_n + j) % len(keywords)] if keywords else None)
        yn_keywords.append(assigned_kw)
        yn_meta.append(meta)

    # Generate all YN questions in one call
    if yn_excerpts:
        yn_results = _generate_batch_questions(yn_excerpts, seed + 100, yn_keywords, YN_TEMPLATE, difficulty_profile)
        for j, (q, kw, meta) in enumerate(zip(yn_results, yn_keywords, yn_meta)):
            qid = f"q-{topic}-{docset_hash[:6]}-yn-{j+1}"
            questions.append(_create_question_object(q, qid, kw, meta))

    demo_user = "\n\n".join(_trim(p[0], 200) for p in pool[:8])
    return {
        "questions": questions,
        "promptHash": prompt_hash(demo_user)
    }
