# Embedding Cache — Question Generation Pipeline

## Problem

The question generation (QG) pipeline uses cosine similarity between keyword embeddings and chunk embeddings to select the most relevant text chunks for each question. Without caching, the system re-embeds all chunks (240+ per topic) on every quiz request. With `all-mpnet-base-v2` (768-dim), this takes 3–4 minutes on CPU — added on top of the 6–7 minutes of LLM generation per quiz.

## Solution: Three-Tier Embedding Cache

The caching system eliminates re-embedding entirely by loading pre-computed vectors from ChromaDB (which stores them at ingestion time).

### Tier 1 — Module-Level In-Memory Cache

**File:** `rag/qg.py` (line 24)

```python
_chunk_emb_cache: Dict[Tuple[str, str, str], np.ndarray] = {}
```

A Python dict keyed by `(topic, docset_hash, emb_model)` holding a NumPy array of shape `(n_chunks, embedding_dim)`. Lives for the lifetime of the FastAPI process. Once populated, all subsequent quiz requests for the same topic skip embedding entirely.

### Tier 2 — Startup Warmup via FastAPI Lifespan

**File:** `api/main.py` (lines 7–11), `rag/qg.py` (lines 27–53)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from rag.qg import warmup_chunk_cache
    warmup_chunk_cache()
    yield
```

`warmup_chunk_cache()` runs once when FastAPI starts. It iterates over all topics in `docsets.json`, fetches their stored embeddings from ChromaDB (via `include=["embeddings"]`), and populates `_chunk_emb_cache`. No model inference occurs — ChromaDB already stores the vectors from ingestion.

### Tier 3 — ChromaDB Stored Embeddings (Fallback)

**File:** `rag/qg.py` (lines 106–162)

If a topic isn't in the in-memory cache (e.g., newly ingested after startup), `generate_qg` calls `_ordered_chunks(col, topic, hash, include_embeddings=True)`. ChromaDB returns the stored vectors alongside the documents. These are reordered to match the round-robin pool order and cached for future requests.

The round-robin reordering is necessary because ChromaDB returns chunks in its internal order, but the QG pipeline interleaves chunks across PDF sources to ensure balanced coverage. The `pool_orig_indices` list tracks the mapping so embeddings stay aligned with their chunks.

### Fallback — Re-Embedding

If ChromaDB has no stored embeddings (e.g., data migrated from an older ingestion that didn't store vectors), the system falls back to computing embeddings via `SentenceTransformerEmbeddingFunction`. This is logged as a warning and the result is cached to avoid repeating it.

## Cache Invalidation

The cache key includes `docset_hash` — a SHA-256 of the source file signatures (name, size, mtime). When PDFs change, re-ingestion produces a new hash, so the old cache entry is never hit. No explicit invalidation is needed.

Restarting FastAPI clears the in-memory cache; the lifespan warmup repopulates it from ChromaDB.

## Performance Impact

| Scenario | Embedding Time | Total Quiz Time |
|----------|---------------|-----------------|
| No cache (re-embed 240 chunks with mpnet) | ~3–4 min | ~10+ min |
| Cached (warm or ChromaDB load) | ~0 ms | ~6–7 min (LLM only) |
| Startup warmup | ~1 sec per topic | N/A |

## Files Involved

| File | Role |
|------|------|
| `rag/qg.py` | Cache dict, warmup function, `_ordered_chunks`, `generate_qg` |
| `api/main.py` | Lifespan hook calling `warmup_chunk_cache()` |
| `rag/settings.py` | `read_docsets_meta()` — provides topic list for warmup |
| `rag/vecstore.py` | `collection_for()` — ChromaDB collection access |
