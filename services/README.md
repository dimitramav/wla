# WLA RAG Service

FastAPI service that owns the retrieval-augmented generation pipeline for WLA. Express (`api/`) never talks to ChromaDB or Ollama directly — every retrieval, summarization, and question-generation call is proxied through this service at `http://localhost:8000`.

## Folder Map

| Path | Role |
|------|------|
| `api/` | FastAPI app factory (`main.py`) and route modules: `health`, `ingest`, `docsets`, `summary`, `qg` |
| `rag/` | Retrieval pipeline — `ingest.py`, `pdf_filter.py`, `vecstore.py`, `qg.py`, `summary.py`, `settings.py` |
| `llm/` | Ollama client (`client.py`) and prompt templates (`prompts.py`) |
| `cli/ingest_cli.py` | Command-line wrapper around `POST /rag/ingest/{topic}` |
| `benchmarks/` | Evaluation harnesses with their own [README](benchmarks/README.md) and methodology docs |
| `chroma_db/` | Persistent vector store (gitignored) |
| `server.ipynb` | Start the FastAPI server locally |
| `setup.ipynb` | One-time dependency install |

## End-to-End Flow

```
content/<topic>/*.pdf
     │
     ▼  ingestion (one-time, on content change)
ChromaDB (chroma_db/) + docsets.json
     │
     ▼  retrieval (per quiz request)
top-k chunks for keyword(s)
     │
     ▼  generation (per question)
Ollama (gemma2:9b-instruct-q4_0)
     │
     ▼
structured JSON question → Express → browser
```

Two distinct lifecycle moments:

- **Ingestion** runs *once* per docset change. It transforms raw PDFs into a queryable vector store.
- **Retrieval + generation** run *per quiz request*. They reuse the ingested store; embeddings are cached so no model inference is repeated across requests (see [EMBEDDING_CACHE.md](EMBEDDING_CACHE.md)).

## Ingestion Pipeline

Stages (`rag/ingest.py::ingest_topic`):

1. **Collect** — walk `content/<topic>/` for `.pdf`, `.md`, `.txt` (skipping `pdfs_original/`).
2. **Hash** — SHA-256 over each file's `(name, size, mtime)`. This `docset_hash` pins every cached quiz to the exact files it was generated from.
3. **Short-circuit** if the hash is unchanged and `--force` is not set.
4. **Reset the Chroma collection** if the hash changed.
5. **Filter** — `pdf_filter.filter_document` strips boilerplate (headers, footers, references, table-only pages).
6. **Chunk** — LangChain `RecursiveCharacterTextSplitter` with configurable `chunk_size` / `chunk_overlap`.
7. **Quality-filter chunks** — `_is_quality_chunk` rejects chunks dominated by table markup, statistical notation, copyright boilerplate, or author affiliations.
8. **Embed + upsert** — embeddings are computed by Chroma's `SentenceTransformer` embedding function and stored on disk.
9. **Write metadata** — `rag/docsets.json` records hash, file signatures, chunk count, and timestamp.

### Running ingestion

FastAPI must be running on port 8000 (`./scripts/start.sh --fastapi-only` or the full stack).

```bash
# Default chunking (800/100), re-ingest only if files changed
python services/cli/ingest_cli.py --topic school_anxiety

# Custom chunking, force re-ingest
python services/cli/ingest_cli.py --topic school_anxiety \
    --chunk-size 1024 --overlap 200 --force
```

Equivalent direct call:

```bash
curl -X POST "http://localhost:8000/rag/ingest/school_anxiety?force=true&chunk_size=1024&chunk_overlap=200"
```

### CLI parameters

| Flag | Default | Notes |
|------|---------|-------|
| `--topic` | required | Must match a folder name under `content/` |
| `--chunk-size` | `800` | Clamped server-side to `[100, 4000]` |
| `--overlap` | `100` | Clamped to `[0, 1000]` |
| `--force` | `false` | Re-ingest even if the docset hash hasn't changed |
| `--base-url` | `http://localhost:8000` | Override the FastAPI host |

### When to re-run

- New, replaced, or removed PDFs in `content/<topic>/`
- Experimenting with chunking parameters
- Changing the embedding model via `RAG_EMBEDDING_MODEL` in `.env` (use `--force`)

## Retrieval + Generation (Per Request)

- **`/qg`** ([`rag/qg.py`](rag/qg.py)) — for each requested keyword, embeds the keyword, retrieves top-k chunks by cosine similarity (or hybrid BM25+dense — see [methodology_hybrid_search.md](methodology_hybrid_search.md)), feeds them to Ollama with the prompt templates in [`llm/prompts.py`](llm/prompts.py), and parses the structured JSON response.
- **`/summary`** ([`rag/summary.py`](rag/summary.py)) — generates a stable summary per docset; cached by docset hash and regenerated only when the hash changes.
- **`/docsets`** — read-only view of `docsets.json`; lets Express discover the current hash for a topic.
- **`/health`** — liveness probe used by `start.sh`.

Determinism is enforced with `temperature=0` and a fixed seed throughout the pipeline.

## Configuration

Resolved in `rag/settings.py`, with environment overrides:

| Var | Default | Used for |
|-----|---------|----------|
| `RAG_CONTENT_DIR` | `../content` | Source documents |
| `RAG_CHROMA_DIR` | `rag/chroma` | Vector store on disk |
| `RAG_DOCSETS_META` | `rag/docsets.json` | Per-topic metadata |
| `RAG_EMBEDDING_MODEL` | `sentence-transformers/all-mpnet-base-v2` | Embedding model id |

## Related Docs

- [EMBEDDING_CACHE.md](EMBEDDING_CACHE.md) — three-tier embedding cache; why no re-embedding happens per quiz request.
- [methodology_hybrid_search.md](methodology_hybrid_search.md) — research methodology for hybrid dense + BM25 retrieval.
- [benchmarks/README.md](benchmarks/README.md) — RAG and LLM benchmark harnesses, plus pointers to methodology and report docs.
