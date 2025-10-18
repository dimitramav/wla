# This file defines the API route for generating summaries for a specific topic in the RAG (Retrieval-Augmented Generation) system.
# Exposes:
# - GET /rag/summary : Generates a summary for the specified topic and document set hash.
#
# Implementation notes:
# - Uses `read_docsets_meta` to fetch metadata about document sets.
# - Uses `summarize_topic` to generate the summary based on the topic, hash, and seed.
# - Defaults to the latest document set hash if none is provided.

from fastapi import APIRouter, HTTPException, Query
from rag.settings import read_docsets_meta
from rag.summary import summarize_topic

router = APIRouter()

# Route to generate a summary for a specific topic

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
