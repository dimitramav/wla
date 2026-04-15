"""
 * ingest.py
 *
 * This file defines the ingestion logic for processing and storing document data for a specific topic in the RAG (Retrieval-Augmented Generation) system.
 *
 * Key Features:
 * - Collects and processes PDF, Markdown, and text files for a given topic.
 * - Splits text into chunks and stores them in a vector store.
 * - Computes and updates metadata for document sets.
 *
 * Dependencies:
 * - ChromaDB for vector storage.
 * - Document filtering and text splitting utilities.
 * - Metadata management utilities.
"""

import hashlib, re, time
from typing import Dict, Any, List
from fastapi import HTTPException
from .settings import (
    collect_documents, compute_docset_hash, read_docsets_meta, write_docsets_meta
)
from .pdf_filter import filter_document
from .vecstore import make_splitter, collection_for


# Minimum characters of actual prose content for a chunk to be useful
_MIN_PROSE_CHARS = 80

def _is_quality_chunk(text: str) -> bool:
    """Return True if a chunk has enough substantive prose for question generation."""
    # Strip markdown formatting to measure actual content
    clean = re.sub(r'<!--.*?-->', '', text)
    clean = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', clean)
    clean = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', clean)  # keep link text
    clean = re.sub(r'#+\s*', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    if len(clean) < _MIN_PROSE_CHARS:
        return False

    # Reject chunks that are mostly table markup (pipes dominate)
    pipe_count = text.count('|')
    if pipe_count > 10 and pipe_count > len(text) / 40:
        return False

    # Reject chunks that are mostly statistical notation (p-values, medians, etc.)
    stat_chars = len(re.findall(r'[<>=±]\s*\d|p\s*[<>=]|\d+\.\d{2,}', clean))
    if stat_chars > 5 and stat_chars > len(clean) / 30:
        return False

    return True

# Ingest a topic into the vector store
"""
 * ingest_topic
 *
 * Processes and stores document data for a specific topic.
 *
 * Parameters:
 * - topic: The name of the topic to ingest.
 * - force: A boolean indicating whether to force re-ingestion (default: False).
 *
 * Returns:
 * - A dictionary containing the ingestion status, document set hash, and metadata.
 *
 * Workflow:
 * - Collects PDF files for the topic.
 * - Computes a hash for the document set.
 * - Resets the vector store collection if the document set has changed.
 * - Splits text into chunks and stores them in the vector store.
 * - Updates metadata for the document set.
 *
 * Raises:
 * - HTTPException (404): If no PDFs are found for the topic.
"""

def ingest_topic(topic: str, force: bool = False, chunk_size: int = 800, chunk_overlap: int = 100, emb_model: str = None) -> Dict[str, Any]:
    docs_files = collect_documents(topic)
    if not docs_files:
        raise HTTPException(status_code=404, detail=f"No documents found for topic '{topic}'")

    h = compute_docset_hash(docs_files)
    meta = read_docsets_meta()
    prev = meta.get(topic)

    # Short-circuit if unchanged
    if prev and prev.get("hash") == h and not force:
        return {"topic": topic, "docset_hash": h, "status": "unchanged",
                "chunks_upserted": 0, "files": prev.get("files", [])}

    col = collection_for(topic, emb_model)
    # If changed, reset collection (cheap & predictable in prototypes)
    if prev and prev.get("hash") and prev["hash"] != h:
        client = col._client  # internal, but fine for prototype
        client.delete_collection(col.name)
        col = collection_for(topic, emb_model)

    splitter = make_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs, metas, ids = [], [], []

    for p in docs_files:
        filt = filter_document(p)
        text = filt["text"]
        if not text:
            continue

        chunks = splitter.split_text(text)
        skipped = 0
        for i, ch in enumerate(chunks):
            if not _is_quality_chunk(ch):
                skipped += 1
                continue
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
        if skipped:
            print(f"  [{p.name}] skipped {skipped} low-quality chunks")

    if docs:
        # Embeddings are computed HERE by Chroma (via the embedding function)
        col.upsert(ids=ids, documents=docs, metadatas=metas)

    files_meta = [{"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime} for p in docs_files]
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
