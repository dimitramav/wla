import hashlib, time
from typing import Dict, Any, List
from fastapi import HTTPException
from .settings import (
    collect_pdf_files, compute_docset_hash, read_docsets_meta, write_docsets_meta
)
from .pdf_filter import filter_research_pdf
from .vecstore import make_splitter, collection_for

def ingest_topic(topic: str, force: bool = False) -> Dict[str, Any]:
    pdfs = collect_pdf_files(topic)
    if not pdfs:
        raise HTTPException(status_code=404, detail=f"No PDFs found for topic '{topic}'")

    h = compute_docset_hash(pdfs)
    meta = read_docsets_meta()
    prev = meta.get(topic)

    # Short-circuit if unchanged
    if prev and prev.get("hash") == h and not force:
        return {"topic": topic, "docset_hash": h, "status": "unchanged",
                "chunks_upserted": 0, "files": prev.get("files", [])}

    col = collection_for(topic)
    # If changed, reset collection (cheap & predictable in prototypes)
    if prev and prev.get("hash") and prev["hash"] != h:
        from chromadb import PersistentClient
        from chromadb.config import Settings
        # Drop and recreate
        client = col._client  # internal, but fine for prototype
        client.delete_collection(col.name)
        col = client.get_or_create_collection(name=col.name, embedding_function=col._embedding_function)

    splitter = make_splitter()
    docs, metas, ids = [], [], []

    for p in pdfs:
        filt = filter_research_pdf(p)
        text = filt["text"]
        if not text:
            continue

        chunks = splitter.split_text(text)
        for i, ch in enumerate(chunks):
            uid = hashlib.md5(f"{p.name}:{i}:{h}".encode("utf-8")).hexdigest()
            ids.append(f"{p.name}-{i}-{uid}")
            docs.append(ch)
            metas.append({
                "topic": topic,
                "source": p.name,
                "chunk_index": i,
                "docset_hash": h,
                "filter_notes": filt["notes"],
            })

    if docs:
        # Embeddings are computed HERE by Chroma (via the embedding function)
        col.upsert(ids=ids, documents=docs, metadatas=metas)

    files_meta = [{"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime} for p in pdfs]
    # Optionally store fresh count
    try:
        chunk_count = col.count()
    except Exception:
        chunk_count = None

    meta[topic] = {
        "hash": h,
        "files": files_meta,
        "collection": col.name,
        "updated_at": int(time.time()),
        "chunk_count": chunk_count,
    }
    write_docsets_meta(meta)

    return {"topic": topic, "docset_hash": h, "status": "ingested",
            "chunks_upserted": len(docs), "files": files_meta}
