from fastapi import FastAPI
from .routes import health,ingest,docsets,summary,qg

def create_app() -> FastAPI:
    app = FastAPI(title="WLA RAG", version="0.1.0")

    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(docsets.router)
    app.include_router(summary.router)
    app.include_router(qg.router)


    return app
