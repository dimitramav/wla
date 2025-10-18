# This file defines the API route for retrieving metadata about document sets (docsets) for a given topic.
#
# Exposes:
# - GET /rag/docsets/{topic} : Retrieves metadata and chunk count for the specified topic.

from fastapi import APIRouter, HTTPException
from rag.vecstore import collection_for
from rag.settings import read_docsets_meta

router = APIRouter()

@router.get("/rag/docsets/{topic}")
def rag_docset(topic: str):
    meta = read_docsets_meta()
    if topic not in meta:
        raise HTTPException(status_code=404, detail="Unknown topic")
    try:
        n = collection_for(topic).count()
    except Exception:
        n = meta[topic].get("chunk_count")
    return {"topic": topic, **meta[topic], "chunk_count": n}
