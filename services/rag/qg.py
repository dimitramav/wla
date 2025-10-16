from typing import List, Dict, Tuple, Optional
from .vecstore import collection_for
from .settings import read_docsets_meta
from llm.prompts import SYSTEM_QG, USER_QG_MC_TEMPLATE, USER_QG_YN_TEMPLATE
from llm.client import generate_json, prompt_hash

# Limits for the MVP
MAX_CHARS_PER_Q = 450   # excerpt slice per question
POOL_TOP = 24           # take first N chunks as the candidate pool (stable)

def _ordered_chunks(col, topic: str, docset_hash: str) -> List[Tuple[str, Dict]]:
    """
    Returns a stably-ordered list of (text, meta) filtered by topic+hash,
    same philosophy as summarize_topic().
    """
    records = col.get(
        where={"$and": [{"topic": topic}, {"docset_hash": docset_hash}]},
        include=["documents", "metadatas"]
    )
    docs = records.get("documents", []) or []
    metas = records.get("metadatas", []) or []
    pairs = list(zip(docs, metas))
    pairs.sort(key=lambda x: (x[1].get("source",""),
                              x[1].get("page", 0),
                              x[1].get("chunk_idx", 0)))
    return pairs[:POOL_TOP]

def _trim(text: str, n: int) -> str:
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + "…"


def _pick_plan_by_keywords(
    pool: List[Tuple[str, Dict]],
    keywords: List[str],
    needed: int
) -> List[Tuple[str, Dict, Optional[str]]]:
    """
    Deterministic, minimal selection:
    1) Prefer chunks that contain ANY keyword (case-insensitive); tag with the FIRST matching keyword.
    2) If still short, backfill from the top of the pool (tag=None).
    """
    kws = [k.strip().lower() for k in (keywords or []) if k and k.strip()]
    used = set()
    plan: List[Tuple[str, Dict, Optional[str]]] = []

    # Phase 1: keyword matches
    if kws:
        for idx, (txt, meta) in enumerate(pool):
            if len(plan) >= needed:
                break
            low = txt.lower()
            for k in kws:
                if k in low:
                    plan.append((txt, meta, k))
                    used.add(idx)
                    break

    # Phase 2: backfill
    if len(plan) < needed:
        for idx, (txt, meta) in enumerate(pool):
            if len(plan) >= needed:
                break
            if idx in used:
                continue
            plan.append((txt, meta, None))
            used.add(idx)

    return plan[:needed]

def _gen_one_mcq(excerpt: str, seed: int, keyword: Optional[str], dp:Optional[Dict] = None) -> Dict:
    user = USER_QG_MC_TEMPLATE.format(excerpt=excerpt, context_span=dp.get("context_span", 1),
        distractor_strength=dp.get("distractor_strength", 1),
        application_share=int(dp.get("application_share", 0.0) * 100))
    if keyword:
        user += f"\n\nFocus on concept: {keyword}"
    out = generate_json(SYSTEM_QG, user, seed=seed, temperature=0.0)

    if not isinstance(out, dict):
        out = {}

    out.setdefault("text", "What is the main idea?")
    out.setdefault("options", ["A) ...", "B) ...", "C) ...", "D) ..."])
    out.setdefault("correct", "B")
    out.setdefault("why", "Grounded in the excerpt.")
    out["kind"] = "mcq"

    opts = out["options"]
    if len(opts) != 4:
        opts = ["A) ...", "B) ...", "C) ...", "D) ..."]
    out["options"] = opts

    corr = str(out["correct"]).strip().upper().replace(")", "")
    out["correct"] = corr if corr in {"A", "B", "C", "D"} else "B"

    return out

def _gen_one_yn(excerpt: str, seed: int, keyword: Optional[str], dp: Optional[Dict] = None) -> Dict:
    user = USER_QG_YN_TEMPLATE.format(excerpt=excerpt, context_span=dp.get("context_span", 1),
        distractor_strength=dp.get("distractor_strength", 1),
        application_share=int(dp.get("application_share", 0.0) * 100))
    if keyword:
        user += f"\n\nFocus on concept: {keyword}"
    out = generate_json(SYSTEM_QG, user, seed=seed, temperature=0.0)

    if not isinstance(out, dict):
        out = {}

    out.setdefault("text", "Is the statement correct?")
    out.setdefault("correct", "Yes")
    out.setdefault("why", "Grounded in the excerpt.")
    out["kind"] = "yesno"
    out["options"] = ["Yes", "No"]

    corr = str(out["correct"]).strip().lower()
    out["correct"] = "Yes" if corr.startswith("y") else "No"

    return out

def generate_qg(topic: str, docset_hash: str, mix: Dict, seed: int, keywords: List[str], difficulty_profile: Dict = {}) -> Dict:
    """
    Returns:
      {
        "questions": [{ id, kind, text, options, correct, why, keywords, source_spans }],
        "promptHash": "..."
      }
    """
    col = collection_for(topic)
    pool = _ordered_chunks(col, topic, docset_hash)
    if not pool:
        return {"questions": [], "promptHash": ""}

    mcq_n = int(mix.get("mcq", 10))
    yn_n  = int(mix.get("yesno", 5))
    total_needed = mcq_n + yn_n

    plan = _pick_plan_by_keywords(pool, keywords, total_needed)
    questions: List[Dict] = []

    # MCQs
    for i in range(min(mcq_n, len(plan))):
        text, meta, matched_kw = plan[i]
        excerpt = _trim(text, MAX_CHARS_PER_Q)

        # If no match, round-robin assign a keyword so we don't always use the first one.
        assigned_kw = matched_kw or (keywords[i % len(keywords)] if keywords else None)

        q = _gen_one_mcq(excerpt, seed=+ i, keyword=assigned_kw, dp=difficulty_profile)
        qid = f"q-{topic}-{docset_hash[:6]}-mcq-{i+1}"
        questions.append({
            "id": qid,
            "kind": "mcq",
            "text": q["text"],
            "options": q["options"],
            "correct": q["correct"],
            "why": q["why"],
            "keywords": [assigned_kw] if assigned_kw else [],
            "source_spans": [{
                "doc": meta.get("source",""),
                "page_from": meta.get("page", 0),
                "page_to": meta.get("page", 0),
                "chunk_id": f"{meta.get('source','')}-p{meta.get('page',0)}-c{meta.get('chunk_idx',0)}"
            }]
        })

    # Yes/No
    start = mcq_n
    for j in range(min(yn_n, max(0, len(plan) - start))):
        text, meta, matched_kw = plan[start + j]
        excerpt = _trim(text, MAX_CHARS_PER_Q)

        assigned_kw = matched_kw or (keywords[(start + j) % len(keywords)] if keywords else None)

        q = _gen_one_yn(excerpt, seed= 100 + j, keyword=assigned_kw, dp=difficulty_profile)
        qid = f"q-{topic}-{docset_hash[:6]}-yn-{j+1}"
        questions.append({
            "id": qid,
            "kind": "yesno",
            "text": q["text"],
            "options": ["Yes","No"],
            "correct": q["correct"],
            "why": q["why"],
            "keywords": [assigned_kw] if assigned_kw else [],
            "source_spans": [{
                "doc": meta.get("source",""),
                "page_from": meta.get("page", 0),
                "page_to": meta.get("page", 0),
                "chunk_id": f"{meta.get('source','')}-p{meta.get('page',0)}-c{meta.get('chunk_idx',0)}"
            }]
        })

    demo_user = "\n\n".join(_trim(p[0], 200) for p in pool[:8])
    phash = prompt_hash(demo_user)
    return {"questions": questions, "promptHash": phash}
