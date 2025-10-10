from fastapi import FastAPI, HTTPException, Path, Query
from .settings import read_docsets_meta
from .vecstore import collection_for
from .ingest import ingest_topic
from .settings import read_docsets_meta
from .summary import summarize_topic 

def create_app() -> FastAPI:
    app = FastAPI(title="WLA RAG", version="0.1.0")

    @app.get("/health")
    def health():
        return {"ok": True, "service": "fastapi"}

    # Path-param endpoint as you requested
    @app.post("/rag/ingest/{topic}")
    def rag_ingest(topic: str = Path(..., description="Folder under /content"),
                   force: bool = Query(False)):
        return ingest_topic(topic, force=force)

    # Merge metadata + count (keeps API lean)
    @app.get("/rag/docsets/{topic}")
    def rag_docset(topic: str):
        meta = read_docsets_meta()
        if topic not in meta:
            raise HTTPException(status_code=404, detail="Unknown topic")
        # ensure live count is visible (but keep meta pure if you prefer)
        try:
            n = collection_for(topic).count()
        except Exception:
            n = meta[topic].get("chunk_count")
        return {"topic": topic, **meta[topic], "chunk_count": n}
    
    @app.get("/rag/summary")
    def rag_summary(
    topic: str = Query(...),
    hash: str | None = None,
    seed: int = 7,
    ):
        meta = read_docsets_meta()  # reads services/rag/docsets.json
        if topic not in meta:
            raise HTTPException(404, f"topic '{topic}' not found")
        docset_hash = hash or meta[topic]["hash"]
        out = summarize_topic(topic, docset_hash, seed=seed)
        print("Summary generated:", out)
        return {
            "topic": topic,
            "hash": docset_hash,
            "bullets": out["bullets"],
            "promptHash": out["promptHash"],
        }
    

    return app
