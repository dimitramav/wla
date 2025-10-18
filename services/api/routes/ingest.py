# This file defines the API route for ingesting data for a specific topic into the RAG system.
# POST /rag/ingest/{topic} : Triggers ingestion for the specified topic.
# Supports an optional `force` query parameter to re-ingest data.

from fastapi import APIRouter, Path, Query
from rag.ingest import ingest_topic

router = APIRouter()

# Route to trigger ingestion for a specific topic

@router.post("/rag/ingest/{topic}")
def rag_ingest(topic: str = Path(...), force: bool = Query(False)):
    return ingest_topic(topic, force=force)
