# WLA Error Reference

All error codes, HTTP statuses, exceptions, and internal error strings across the three-tier stack.

---

## FastAPI Service (port 8000)

### HTTP Exceptions

| Status | Detail message | Where raised | Cause |
|--------|---------------|--------------|-------|
| `404` | `No PDFs found for topic '{topic}'` | `rag/ingest.py` | Ingest requested for a topic with no PDF files in the content directory |
| `404` | `topic '{topic}' not found` | `api/routes/summary.py` | Summary requested for a topic that has no ChromaDB collection |
| `404` | `Unknown topic` | `api/routes/docsets.py` | Docset lookup for a topic that doesn't exist |
| `422` | `Not enough sources found for that topic. Please broaden your scope or try another topic.` | `api/routes/qg.py` | ChromaDB returned an empty chunk pool for the given topic + docset hash |
| `500` | `LLM generated malformed JSON.` | `api/routes/qg.py` | Ollama response could not be parsed as JSON after all retries |

### Internal Python Exceptions

| Exception | Where raised | Where caught | Behaviour |
|-----------|-------------|--------------|-----------|
| `json.JSONDecodeError` | `llm/client.py → generate_json` | `rag/qg.py → _generate_question` (per retry) | Retry consumed; falls back to default question after `MAX_RETRIES=2` |
| `json.JSONDecodeError` | `llm/client.py → generate_json` | `api/routes/qg.py` | Converted to `HTTPException(500)` |
| `requests.HTTPError` | `llm/client.py` (`r.raise_for_status()`) | Uncaught — propagates to FastAPI default handler | Ollama returned a non-2xx response; FastAPI returns 500 |

---

## Express API (port 3001)

### Auth routes (`/auth`)

| Status | Error code / body | Endpoint | Cause |
|--------|------------------|----------|-------|
| `400` | `{ code: "BAD_REQUEST" }` | `POST /auth/register` | Missing or malformed request body fields |
| `400` | `{ code: "BAD_REQUEST" }` | `POST /auth/login` | Missing or malformed credentials |
| `401` | `{ code: "INVALID_CREDENTIALS" }` | `POST /auth/login` | Wrong email or password |
| `401` | `{ code: "UNAUTHORIZED" }` | Any protected route | Missing or invalid JWT cookie (`wla`) |
| `204` | — | `POST /auth/logout` | Success — cookie cleared |
| `409` | `{ code: "EMAIL_TAKEN" }` | `POST /auth/register` | Email already registered in MongoDB |

### Quiz routes (`/quiz`)

| Status | Error message | Endpoint | Cause |
|--------|--------------|----------|-------|
| `400` | `Invalid level` | `POST /quiz/start` | `level` not in allowed values |
| `400` | `Missing or invalid uid` | `POST /quiz/start` | `uid` missing or not a valid ObjectId |
| `400` | `Missing or invalid docset` | `POST /quiz/start` | `docset` hash missing or malformed |
| `400` | `No keywords for level` | `POST /quiz/start` | `keywords.yaml` has no entries for the requested level |
| `400` | `Missing required fields` | `POST /quiz/submit` | Answer submission missing `quizId`, `answers`, or `uid` |
| `404` | `Quiz not found` | `POST /quiz/submit` | `quizId` not found in MongoDB |
| `500` | `Failed to start quiz` | `POST /quiz/start` | Unexpected error during quiz creation |
| `502` | `QG invalid response` | `POST /quiz/start` | FastAPI `/qg` returned a non-2xx or malformed response |

### Topics / Summary routes (`/topics`)

| Status | Error code | Endpoint | Cause |
|--------|-----------|----------|-------|
| `404` | `docset_not_found` | `GET /topics/:id/docset` | No live docset hash found for the topic |
| `500` | `topics_load_failed` | `GET /topics` | MongoDB read error |
| `502` | `rag_summary_failed` | `GET /topics/:id/summary` | FastAPI `/rag/summary` unreachable or returned an error |

### Progress routes (`/progress`)

| Status | Error body | Endpoint | Cause |
|--------|-----------|----------|-------|
| `400` | `{ code: "bad_request", message: "Missing or invalid userId" }` | `GET /progress` | `userId` param missing or invalid |
| `500` | `{ code: "progress_failed", message: "Failed to load/create progress" }` | `GET /progress` | MongoDB read/write error |

### Internal JS errors (thrown, not HTTP)

| Error string | Where thrown | Where caught | Behaviour |
|-------------|-------------|--------------|-----------|
| `EMAIL_TAKEN` | `db/UserDB.js` | `routes/auth.js` | Mapped to HTTP 409 |
| `INVALID_CREDENTIALS` | `db/UserDB.js` | `routes/auth.js` | Mapped to HTTP 401 |
| `CORS not allowed for origin: {origin}` | `server.js` | Express CORS middleware | Request rejected at middleware level |
| `FastAPI ${status}` | `ragClient.js → getSummaryFromRag` | Route catch block | Generic FastAPI proxy error for summary endpoint |
| `{body.detail}` or `QG failed: ${status}` | `ragClient.js → qg` | `routes/quiz.js` | FastAPI detail forwarded to quiz route error handler |

---

## LLM / Ollama Layer

| Condition | Behaviour |
|-----------|-----------|
| Ollama returns non-2xx | `requests.HTTPError` raised via `r.raise_for_status()` — propagates up as FastAPI 500 |
| Ollama returns non-JSON text | `_extract_first_json` attempts fallback extraction; returns `None` if all parsing fails |
| `None` from `_extract_first_json` | `generate_json` raises `json.JSONDecodeError` |
| `json.JSONDecodeError` in `_generate_question` | Retry consumed (up to `MAX_RETRIES = 2`); default fallback question used on exhaustion |
| All retries exhausted + route catches error | `HTTPException(500, "LLM generated malformed JSON.")` |

---

## Retry & Fallback Policy

| Layer | Max retries | Fallback |
|-------|------------|---------|
| `_generate_question` (LLM call) | 2 | Default question: `"What is the main idea?"` / `"Is the statement correct?"` |
| `generate_bullets` (summary LLM call) | None | `requests.HTTPError` propagates |
| Express → FastAPI proxy | None | HTTP 502 returned to frontend |

---

## Frontend Error Handling

Errors from the Express API surface in the React UI. The `ragClient.js` layer forwards FastAPI `detail` strings directly, so toast messages shown to users originate from this table's **Detail message** column.

---

*Last updated: 2026-03-29 — BUGS-01 (added 422/500 handling and detail forwarding)*
