from fastapi import APIRouter, HTTPException, Query
from rag.settings import read_docsets_meta
from rag.summary import summarize_topic

router = APIRouter()

@router.get("/rag/summary")
def rag_summary(
    topic: str = Query(...),
    hash: str | None = None,
    seed: int = 7,
):
    meta = read_docsets_meta()
    if topic not in meta:
        raise HTTPException(404, f"topic '{topic}' not found")
    docset_hash = hash or meta[topic]["hash"]
    out = summarize_topic(topic, docset_hash, seed=seed)
    return {
        "topic": topic,
        "hash": docset_hash,
        "bullets": out["bullets"],
        "promptHash": out["promptHash"],
    }
