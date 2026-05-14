from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routes import health,ingest,docsets,summary,qg,highlight


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm chunk embedding cache on startup
    from rag.qg import warmup_chunk_cache
    warmup_chunk_cache()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="WLA RAG", version="0.1.0", lifespan=lifespan)

    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(docsets.router)
    app.include_router(summary.router)
    app.include_router(qg.router)
    app.include_router(highlight.router)

    return app

app = create_app()
