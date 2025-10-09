from .vecstore import collection_for
from typing import List, Dict

MAX_CHARS = 4500   # keep context small for tiny CPU models
TOP_M     = 30     # take first 30 chunks in stable order

def build_stable_context(col, topic: str, docset_hash: str) -> str:
    # pull all metadata for this topic/version from Chroma
    # we rely on metadata stored at ingest: {"topic":..., "docset_hash":..., "source":..., "page":..., "chunk_idx":...}
    # NOTE: using a filtered get to avoid similarity randomness
    records = col.get(
        where={
            "$and": [
                {"topic": topic},
                {"docset_hash": docset_hash}
            ]
        },
        include=["documents", "metadatas"]
    )
    docs = records.get("documents", [])
    metas = records.get("metadatas", [])
    # stable sort
    ordered = sorted(zip(docs, metas), key=lambda x: (x[1].get("source",""), x[1].get("page", 0), x[1].get("chunk_idx", 0)))
    # take first TOP_M and truncate chars
    buf, total = [], 0
    for d, m in ordered[:TOP_M]:
        seg = f"[{m.get('source')} p{m.get('page')}:#{m.get('chunk_idx')}] {d}\n"
        if total + len(seg) > MAX_CHARS: break
        buf.append(seg); total += len(seg)
    return "".join(buf)

def summarize_topic(topic: str, docset_hash: str, seed: int = 7) -> Dict:
    from llm.prompts import SYSTEM_SUMMARY, USER_TEMPLATE
    from llm.client import generate_bullets, prompt_hash
    col = collection_for(f"topic__{topic}")  # same naming as ingest
    ctx = build_stable_context(col, topic, docset_hash)
    user = USER_TEMPLATE.format(topic=topic, docset_hash=docset_hash) + "\n\n" + ctx
    bullets = generate_bullets(SYSTEM_SUMMARY, user, seed=seed, temperature=0.0)
    return {
        "topic": topic,
        "hash": docset_hash,
        "bullets": bullets,
        "promptHash": prompt_hash(user),
        "seed": seed,
    }
