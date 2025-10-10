from fastapi import APIRouter, Path, Query
from rag.ingest import ingest_topic

router = APIRouter()

@router.post("/rag/ingest/{topic}")
def rag_ingest(topic: str = Path(...), force: bool = Query(False)):
    return ingest_topic(topic, force=force)
