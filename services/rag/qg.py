from typing import List, Dict, Tuple
from .vecstore import collection_for
from .settings import read_docsets_meta
from llm.prompts import SYSTEM_QG, USER_QG_MC_TEMPLATE, USER_QG_YN_TEMPLATE
from llm.client import generate_json, prompt_hash

# Limits for the MVP
MAX_CHARS_PER_Q = 450   # excerpt slice per question
POOL_TOP = 24          # take first N chunks as the candidate pool (stable)

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

def _gen_one_mcq(excerpt: str, seed: int) -> Dict:
    user = USER_QG_MC_TEMPLATE.format(excerpt=excerpt)
    out = generate_json(SYSTEM_QG, user, seed=seed, temperature=0.0)

    # Add fallback/defaults
    if not isinstance(out, dict):
        out = {}

    out.setdefault("text", "What is the main idea?")
    out.setdefault("options", ["A) ...", "B) ...", "C) ...", "D) ..."])
    out.setdefault("correct", "B")
    out.setdefault("why", "Grounded in the excerpt.")
    out["kind"] = "mcq"

    # Enforce normalized options and correct label
    opts = out["options"]
    if len(opts) != 4:
        opts = ["A) ...", "B) ...", "C) ...", "D) ..."]
    out["options"] = opts

    corr = str(out["correct"]).strip().upper().replace(")", "")
    out["correct"] = corr if corr in {"A", "B", "C", "D"} else "B"

    out["why"] = _trim(out.get("why", ""), 140)
    return out


def _gen_one_yn(excerpt: str, seed: int) -> Dict:
    user = USER_QG_YN_TEMPLATE.format(excerpt=excerpt)
    out = generate_json(SYSTEM_QG, user, seed=seed, temperature=0.0)

    if not isinstance(out, dict):
        out = {}

    out.setdefault("text", "Is the statement correct?")
    out.setdefault("correct", "Yes")
    out.setdefault("why", "Grounded in the excerpt.")
    out["kind"] = "yesno"
    out["options"] = ["Yes", "No"]  # enforce exactly two options

    corr = str(out["correct"]).strip().lower()
    out["correct"] = "Yes" if corr.startswith("y") else "No"

    out["why"] = _trim(out.get("why", ""), 140)
    return out


def generate_qg(topic: str, docset_hash: str, mix: Dict, seed: int, keywords: List[str]) -> Dict:
    """
    Returns a dict with:
      {
        "questions": [
          {
            "id","kind","text","options","correct","why",
            "keywords": [...], "source_spans":[{doc,page_from,page_to,chunk_id}]
          }, ...
        ],
        "promptHash": "...",
      }
    """
    col = collection_for(topic)
    pool = _ordered_chunks(col, topic, docset_hash)
    if not pool:
        return {"questions": [], "promptHash": ""}

    mcq_n = int(mix.get("mcq", 10))
    yn_n  = int(mix.get("yesno", 5))

    # Simple round-robin across the pool for determinism
    questions = []
    idx = 0
    # MCQs first
    for i in range(mcq_n):
        text, meta = pool[idx % len(pool)]
        idx += 1
        excerpt = _trim(text, MAX_CHARS_PER_Q)
        q = _gen_one_mcq(excerpt,  i)  # vary seed slightly per item for diversity
        qid = f"q-{topic}-{docset_hash[:6]}-mcq-{i+1}"
        q_out = {
            "id": qid,
            "kind": "mcq",
            "text": q["text"],
            "options": q["options"],
            "correct": q["correct"],
            "why": q["why"],
            "keywords": keywords[:1] if keywords else [],  # simple MVP tag
            "source_spans": [{
                "doc": meta.get("source",""),
                "page_from": meta.get("page", 0),
                "page_to": meta.get("page", 0),
                "chunk_id": f"{meta.get('source','')}-p{meta.get('page',0)}-c{meta.get('chunk_idx',0)}"
            }]
        }
        questions.append(q_out)

    # Yes/No
    for j in range(yn_n):
        text, meta = pool[idx % len(pool)]
        idx += 1
        excerpt = _trim(text, MAX_CHARS_PER_Q)
        q = _gen_one_yn(excerpt, seed= 100 + j)
        qid = f"q-{topic}-{docset_hash[:6]}-yn-{j+1}"
        q_out = {
            "id": qid,
            "kind": "yesno",
            "text": q["text"],
            "options": ["Yes","No"],     # enforce
            "correct": q["correct"],
            "why": q["why"],
            "keywords": keywords[:1] if keywords else [],
            "source_spans": [{
                "doc": meta.get("source",""),
                "page_from": meta.get("page", 0),
                "page_to": meta.get("page", 0),
                "chunk_id": f"{meta.get('source','')}-p{meta.get('page',0)}-c{meta.get('chunk_idx',0)}"
            }]
        }
        questions.append(q_out)

    # overall prompt hash (for caching/debug)
    # build a synthetic "user prompt" fingerprint from the first few excerpts
    demo_user = "\n\n".join(_trim(p[0], 200) for p in pool[:8])
    phash = prompt_hash(demo_user)
    return {"questions": questions, "promptHash": phash}
