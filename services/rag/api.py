from fastapi import FastAPI, HTTPException, Path, Query
from .settings import read_docsets_meta
from .vecstore import collection_for
from .ingest import ingest_lesson
from .settings import read_docsets_meta
from .summary import summarize_lesson 

def create_app() -> FastAPI:
    app = FastAPI(title="WLA RAG", version="0.1.0")

    @app.get("/health")
    def health():
        return {"ok": True, "service": "fastapi"}

    # Path-param endpoint as you requested
    @app.post("/rag/ingest/{lesson}")
    def rag_ingest(lesson: str = Path(..., description="Folder under /content"),
                   force: bool = Query(False)):
        return ingest_lesson(lesson, force=force)

    # Merge metadata + count (keeps API lean)
    @app.get("/rag/docsets/{lesson}")
    def rag_docset(lesson: str):
        meta = read_docsets_meta()
        if lesson not in meta:
            raise HTTPException(status_code=404, detail="Unknown lesson")
        # ensure live count is visible (but keep meta pure if you prefer)
        try:
            n = collection_for(lesson).count()
        except Exception:
            n = meta[lesson].get("chunk_count")
        return {"lesson": lesson, **meta[lesson], "chunk_count": n}
    @app.get("/rag/summary")
    def rag_summary(
    lesson: str = Query(...),
    hash: str | None = None,
    seed: int = 7,
    ):
        meta = read_docsets_meta()  # reads services/rag/docsets.json
        if lesson not in meta:
            raise HTTPException(404, f"Lesson '{lesson}' not found")
        docset_hash = hash or meta[lesson]["hash"]
        out = summarize_lesson(lesson, docset_hash, seed=seed)
        return {
            "lesson": lesson,
            "hash": docset_hash,
            "bullets": out["bullets"],
            "model": out["model"],
            "promptHash": out["promptHash"],
        }
    

    return app
