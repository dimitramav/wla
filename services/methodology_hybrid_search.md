# Hybrid Search Methodology: BM25 + Dense Retrieval via Reciprocal Rank Fusion

**Phase:** RAG Retrieval Logging & Benchmarking ---

## What Is Being Evaluated and Why It Matters

### The role of retrieval in the WLA pipeline

The Watch-Listen-Act platform generates quiz questions for teachers about student
mental health. The full pipeline operates as follows:

```
Academic corpus (8 PDFs)
       ↓  chunked and embedded
ChromaDB vector store
       ↓  retrieval — given a keyword, find the most relevant chunks
Retrieved chunks (up to 24)
       ↓  passed to the language model as context
Mistral 7B generates a quiz question grounded in that chunk
       ↓
Teacher answers the question
```

The quality of each quiz question is entirely determined by which chunks were
retrieved in the middle step. If the retrieval step returns an irrelevant chunk
— for example, a passage about research study methodology when the keyword is
"school refusal" — the language model will generate a question about research
methodology, not about school refusal. The teacher is presented with an off-topic
question and learns nothing useful about the concept they were supposed to practice.

A language model can write a fluent, grammatically correct, and plausible-sounding
question from a completely irrelevant passage. There is no signal in the generated
question itself that retrieval failed. This is what makes retrieval quality the
critical variable to evaluate and optimise: failure is silent and pedagogically
consequential.

### What this benchmark evaluates

This benchmark evaluates **retrieval quality** — specifically: given a concept from
the school anxiety keyword taxonomy (e.g. "somatic complaints", "graduated exposure",
"cognitive restructuring"), does the system retrieve the chunks from the corpus that
actually contain knowledge about that concept?

The language model is not evaluated here. The benchmark does not ask "did Mistral
write a good question?" — that is a separate evaluation covered in the Model
Benchmarking phase (Phase 7, BENCH-01–04). The question being answered is:

> *"Did ChromaDB return the right source material for Mistral to work with?"*

These are two distinct failure modes with different remedies. Retrieval failures are
fixed by changing the embedding model, chunk size, or retrieval algorithm. Generation
failures are fixed by improving the prompt template or changing the language model.
Conflating the two makes diagnosis impossible.

### Measuring retrieval quality with RAGAS

Retrieval quality is scored using RAGAS `context_relevancy` (Shahul Es et al., 2023).
For each question in the golden set, the metric asks a judge language model:

> *"Given this question and these retrieved text chunks, do the chunks contain the
> information needed to answer the question?"*

A high `context_relevancy` score indicates the retrieved chunks genuinely contain
the knowledge about the target concept. A low score indicates the retrieval system
returned off-topic material, regardless of how well the language model might have
used it.

The judge model used for RAGAS evaluation is the same Mistral 7B instance running
locally via Ollama. Using a local model rather than an external API is consistent
with the project's offline-first design and avoids data leaving the local environment.

### Why retrieval configuration is non-trivial for this corpus

The school anxiety corpus contains two document types with substantially different
writing styles:

- **Academic research papers** (six documents): dense technical language, structured
  abstracts, statistical terminology, citation-heavy. Concepts are often named
  precisely ("emotionally based school avoidance", "Okapi BM25").
- **Practitioner guides** (two Anna Freud Centre documents): plain language, scenario-
  based, concrete actionable descriptions ("try to model a calm and measured response",
  "a worry is a thought, not necessarily a fact"). Concepts are described rather than
  named.

An embedding model trained primarily on academic text may represent practitioner
guide chunks poorly, causing the retrieval system to systematically favour research
paper passages even when the practitioner content would produce a more useful quiz
question for a classroom teacher. Conversely, BM25 keyword matching may favour
practitioner text (which uses exact everyday vocabulary matching the taxonomy
keywords) over research text (which uses specialist synonyms).

Chunking strategy compounds this: a 512-character chunk may split a case study
mid-sentence, severing the causal chain between a teacher's action and a student's
response. An 800-character chunk preserves that chain but may blend two unrelated
topics at section boundaries.

Evaluating three embedding models, two chunk sizes, and two retrieval algorithms
across 12 configurations produces empirical evidence for which combination best
serves this specific corpus and teacher training use case, rather than relying on
published benchmark results from unrelated domains.

### How the results feed into the thesis

The benchmark produces a CSV file (`benchmark_results.csv`) with one row per
question per configuration. Aggregating by configuration gives a comparison table:

| Config | Embedding model | Chunks | Retrieval | Avg context_relevancy |
|--------|----------------|--------|-----------|----------------------|
| A | all-MiniLM-L6-v2 | 800/100 | dense | — |
| B | all-MiniLM-L6-v2 | 800/100 | hybrid | — |
| C | all-mpnet-base-v2 | 512/50 | dense | — |
| ... | ... | ... | ... | — |

The top-performing configuration is adopted as the production retrieval setting.
The table, the selection rationale, and a discussion of the observed trade-offs
are written up in **thesis Chapter 5 (Evaluation)** as empirical evidence that
the system's retrieval component was optimised rather than arbitrarily configured.

Additionally, `retrieval_logs.jsonl` records every chunk retrieval during live
teacher usage (RAG-01), providing a continuous observability trail beyond the
one-time benchmark.

---

## Overview

The WLA retrieval pipeline supports two retrieval modes:

| Mode | Algorithm | Description |
|------|-----------|-------------|
| `dense` | Cosine similarity on sentence embeddings | Baseline — captures semantic meaning |
| `hybrid` | Dense + BM25 sparse, merged via RRF | Combines semantic and keyword matching |

The `hybrid` mode is implemented in `services/rag/qg.py` using the `rank_bm25`
library for sparse scoring and Reciprocal Rank Fusion for merging. Both modes are
benchmarked under identical ingestion conditions by `services/benchmarks/rag_benchmark.py`.

---

## How the Hybrid Implementation Works

### Step 1 — Dense retrieval (cosine similarity)

Each taxonomy keyword is embedded using the configured sentence transformer model.
Each chunk in the pool (up to 24, fetched from ChromaDB) is also embedded using
the same model. Cosine similarity is computed between every keyword vector and every
chunk vector. Each chunk is assigned its best similarity score across all keywords,
and the keyword that produced that best score is recorded as the "matched keyword"
for logging. Chunks are ranked by descending best similarity score.

### Step 2 — Sparse retrieval (BM25)

`BM25Okapi` from the `rank_bm25` library is instantiated over the tokenised chunk
pool at query time. The query is formed by joining all keywords into a single string,
lowercased and whitespace-split into tokens. BM25 scores each chunk by how frequently
query tokens appear in it, adjusted for chunk length using the Okapi BM25 variant
(Robertson & Zaragoza, 2009). This produces an independent ranked list from the
dense method: chunks are scored by exact token frequency rather than semantic
embedding proximity.

### Step 3 — Reciprocal Rank Fusion (RRF)

Both retrieval methods produce an independent ranking over the same pool. RRF merges
them into a single unified ranking using the formula from Cormack, Clarke &
Buettcher (SIGIR 2009):

```
RRF_score(chunk_i) = 1 / (k + rank_dense_i) + 1 / (k + rank_sparse_i)
```

`k = 60` is the standard constant from the original paper. Its effect is to dampen
the influence of extreme ranks: a chunk that ranks 1st in dense retrieval but 20th
in BM25 receives a lower combined score than a chunk that ranks 5th in both methods.
This penalises retrieval results that only one method considers relevant and rewards
consistent cross-method agreement — which is a proxy for genuine topical relevance.

The final retrieval order is determined by descending RRF score. Both the dense
cosine score and the BM25 rank are recorded in `retrieval_logs.jsonl` for
observability and thesis analysis.

### Retrieval type as a runtime parameter

The `retrieval_type` parameter in `generate_qg()` (default: `"dense"`) and in
`_pick_plan_by_keywords_hybrid()` controls which path executes:

- `"dense"` → only Steps 1 is executed; BM25 is not instantiated. Behaviour is
  equivalent to the original production retrieval before this phase.
- `"hybrid"` → Steps 1, 2, and 3 are all executed. Falls back to dense-only if
  `rank_bm25` is not installed.

This design means the benchmark can switch retrieval type without reingesting the
corpus, and production stays on the default dense path until the benchmark identifies
a better configuration.

---

## Alternatives Considered

### Alternative 1: LangChain EnsembleRetriever

LangChain provides an `EnsembleRetriever` that wraps multiple retrievers and merges
their results, also using RRF internally.

**Rejected because:**

- It requires wrapping the existing ChromaDB client in LangChain retriever
  abstractions, adding a dependency layer over the directly managed `chromadb` client.
- The `EnsembleRetriever` treats merging as a black box: intermediate dense and
  sparse scores are not separately accessible. The WLA benchmark and retrieval log
  require per-chunk score visibility for observability (RAG-01) and thesis reporting.
- LangChain's public API changes frequently between minor versions. The project
  already pins `langchain-text-splitters` to a narrow range for this reason, and
  introducing a broader LangChain dependency would expand version fragility.

### Alternative 2: MongoDB Text Search + ChromaDB + RRF

MongoDB Atlas supports full-text search. Sparse results from MongoDB could be merged
with ChromaDB dense results via RRF.

**Rejected because:**

- The project architecture strictly separates concerns: FastAPI handles RAG and never
  touches MongoDB; Express handles all database operations (see CLAUDE.md). Introducing
  a MongoDB connection in FastAPI would violate this boundary and create a hidden
  cross-service dependency.
- It would require indexing the corpus documents twice: once in ChromaDB for dense
  retrieval and once in MongoDB for text search. This duplicates storage and creates
  a synchronisation problem whenever the document corpus is updated — the two indexes
  could diverge silently.

### Chosen: Custom `rank_bm25` in memory

**Advantages:**

- `rank_bm25` is a pure-Python library with no server, index file, or external
  infrastructure. The chunk pool (max `POOL_TOP = 24` chunks) is already loaded into
  memory from the ChromaDB fetch, so BM25 instantiation adds negligible latency.
- Dense cosine scores and BM25 scores are both fully accessible before merging,
  enabling per-chunk logging of both scores to `retrieval_logs.jsonl` (RAG-01).
- `retrieval_type` is a runtime parameter, so the benchmark compares both modes under
  identical ingestion and without code changes — only the parameter changes.
- The RRF formula, the `k=60` constant, and BM25 are all directly citable in the
  thesis methodology with primary academic sources.
- The implementation is self-contained in `qg.py`. If the project later outgrows it
  (larger pool sizes, preindexing needed), it can be replaced without architectural
  changes elsewhere.

**Trade-offs:**

- BM25 is recomputed per query from the live pool rather than being preindexed. For
  pools of ≤ 24 chunks this takes under 1ms and is negligible. At pool sizes above
  ~200 chunks a persistent index would be preferable.
- Tokenisation uses naive whitespace splitting (`.lower().split()`). Stopword removal
  or stemming would likely improve sparse recall on practitioner guide text but was
  excluded to keep all configurations comparable under the same tokenisation scheme.

---

## References

- Robertson, S., & Zaragoza, H. (2009). *The Probabilistic Relevance Framework:
  BM25 and Beyond*. Foundations and Trends in Information Retrieval, 3(4), 333–389.
- Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). *Reciprocal Rank Fusion
  Outperforms Condorcet and Individual Rank Learning Methods*. Proceedings of SIGIR
  2009, 758–759.
- Shahul Es, S., James, J., Anke, L. E., & Schockaert, S. (2023). *RAGAS: Automated
  Evaluation of Retrieval Augmented Generation*. arXiv:2309.15217.
