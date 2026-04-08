# This file defines the API route for ingesting data for a specific topic into the RAG system.
# POST /rag/ingest/{topic} : Triggers ingestion for the specified topic.
# Supports optional `force`, `chunk_size`, and `chunk_overlap` query parameters.

from fastapi import APIRouter, Path, Query
from rag.ingest import ingest_topic

router = APIRouter()

# Route to trigger ingestion for a specific topic

@router.post("/rag/ingest/{topic}")
def rag_ingest(
    topic: str = Path(...),
    force: bool = Query(False),
    chunk_size: int = Query(800, ge=100, le=4000),
    chunk_overlap: int = Query(100, ge=0, le=1000),
):
    return ingest_topic(topic, force=force, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
