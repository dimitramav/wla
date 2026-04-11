# WLA Benchmarks — How to Run

This directory contains two independent benchmarks plus offline rescoring tools:

| Benchmark | Entry point | Purpose |
|-----------|-------------|---------|
| RAG retrieval | `benchmarks.rag_benchmark` | Compare embedding × chunk × retrieval-strategy configurations |
| LLM generation | `benchmarks.llm_benchmark` | Compare local generator LLMs on a frozen RAG context set |
| LLM RAGAS rescoring | `benchmarks.llm_ragas_score` | Re-score an existing LLM CSV with RAGAS (no regeneration) |
| Answer-relevancy investigation | `benchmarks.investigations.rescore_answer_metric` | Audit rig for Finding 4 (payload-shape hypothesis) |
| MCQ rubric investigation | `benchmarks.investigations.rescore_mcq_rubric` | Audit rig for Finding 5 (MCQ quality rubric) |

For **what** each benchmark measures and **why**, see [methodologies/RAG_BENCHMARK_METHODOLOGY.md](methodologies/RAG_BENCHMARK_METHODOLOGY.md) and [methodologies/LLM_BENCHMARK_METHODOLOGY.md](methodologies/LLM_BENCHMARK_METHODOLOGY.md). For **results**, see [reports/RAG_BENCHMARK_REPORT.md](reports/RAG_BENCHMARK_REPORT.md) and [reports/LLM_BENCHMARK_REPORT.md](reports/LLM_BENCHMARK_REPORT.md).

---

## 1. Prerequisites (both benchmarks)

1. **Python deps installed:** `pip install -r services/requirements.txt`
2. **PDF corpus ingested** for the target topic (`school_anxiety`). The RAG benchmark will re-ingest per config automatically; the LLM benchmark reads a frozen RAG CSV and does not ingest.
3. **Ollama running** at `http://localhost:11434`. The benchmarks pull and remove models sequentially — disk is managed automatically, but you need connectivity to pull the first time.
4. **`GOOGLE_API_KEY` set** in `.env` or the shell environment. Required by every benchmark that uses the RAGAS judge or the MCQ rubric (i.e. all of them except the cosine-only path of `rag_benchmark`). The judge is Google Gemini 2.5 Flash Lite via `langchain-google-genai`.
5. **FastAPI service up** if you intend to ingest fresh (`./scripts/start.sh --fastapi-only`). Not required for pure rescoring.

Topic, embedding models, chunk sizes, retrieval types, and generator models are all centralised in [config.py](config.py) — edit there to change the matrix.

### Testing protocol

Per the project-wide rule (`CLAUDE.md` → Testing Protocol), always start services through the harness and stop them when done:

```bash
./scripts/start.sh --fastapi-only   # RAG benchmark (re-ingests)
# or
./scripts/start.sh --backend-only   # LLM benchmark (no FastAPI required)
...
./scripts/stop.sh
```

---

## 2. RAG Retrieval Benchmark

**What it does.** Runs all 12 configurations (3 embeddings × 2 chunk sizes × 2 retrieval strategies) against the 10 golden questions. Scores each row with cosine similarity and RAGAS `context_precision`. Writes one CSV with 120 rows to `benchmarks/results/rag_<timestamp>.csv`.

```bash
cd services
python -m benchmarks.rag_benchmark
```

No flags. The run takes **3–4 hours on CPU**, dominated by RAGAS judge calls. Progress is printed to stdout — use `python -u -m benchmarks.rag_benchmark` for unbuffered logs if piping.

**Output:** `services/benchmarks/results/rag_<YYYYMMDD_HHMMSS>.csv` (schema in [config.py::RAG_CSV_FIELDS](config.py)).

---

## 3. LLM Generation Benchmark

**What it does.** For each of the four generator models, generates one MCQ per row from a frozen RAG CSV (120 rows), then scores every generation with format compliance + RAGAS faithfulness + MCQ quality rubric. Writes one CSV with 480 rows to `benchmarks/results/llm_<timestamp>.csv`.

**Must be run after a RAG benchmark** so that a `rag_*.csv` exists to freeze retrieval contexts against. By default, the latest `rag_*.csv` in `results/` is used.

```bash
cd services
# Use the most recent rag_*.csv automatically:
python -m benchmarks.llm_benchmark

# Or pin a specific RAG run:
python -m benchmarks.llm_benchmark --rag-csv rag_20260410_160216.csv
```

The run takes **~8 hours on CPU** (dominated by Ollama generation) plus ~10 minutes for the Gemini judge pass. Each model is `ollama pull`ed, benchmarked, then `ollama rm`ed sequentially to bound disk usage — so the run is resumable only per-model, not per-row.

**Output:** `services/benchmarks/results/llm_<YYYYMMDD_HHMMSS>.csv` (schema in [config.py::LLM_CSV_FIELDS](config.py)).

---

## 4. Offline RAGAS Rescoring (no regeneration)

Re-runs RAGAS faithfulness + MCQ rubric on an existing LLM CSV. Use this when you want to change the scoring pipeline without paying the 8-hour generation cost again.

```bash
cd services
# Rescore the latest llm_*.csv against the latest rag_*.csv:
python -m benchmarks.llm_ragas_score

# Pin a specific pair:
python -m benchmarks.llm_ragas_score \
    --llm-csv llm_20260410_191454.csv \
    --rag-csv rag_20260410_160216.csv

# Force re-score rows that already have scores:
python -m benchmarks.llm_ragas_score --force
```

**Output:** overwrites the input CSV in place with updated score columns.

---

## 5. Investigation Scripts

Both are one-off audit rigs preserved for auditability — see Findings 4 and 5 in [reports/LLM_BENCHMARK_REPORT.md](reports/LLM_BENCHMARK_REPORT.md).

### 5.1 Answer-relevancy payload audit (Finding 4)

Re-parses `raw_output` and re-scores `answer_relevancy` with a shortened payload (just the `why` explanation) to test whether the 0.35–0.38 cluster is a payload-shape artefact. Supports two embedding backends via env flags inside the script.

```bash
cd services
python -m benchmarks.investigations.rescore_answer_metric \
    --llm-csv llm_20260410_191454.csv \
    --rag-csv rag_20260410_160216.csv \
    [--out-csv llm_20260410_191454_rescored.csv] \
    [--limit 20]
```

### 5.2 MCQ quality rubric (Finding 5)

Applies the three-dimension LLM-as-judge rubric (stem clarity, distractor plausibility, pedagogical appropriateness) to every parseable row of an existing LLM CSV.

```bash
cd services
python -m benchmarks.investigations.rescore_mcq_rubric \
    --llm-csv llm_20260410_191454.csv \
    --rag-csv rag_20260410_160216.csv \
    [--out-csv llm_20260410_191454_mcq_rubric.csv] \
    [--limit 20]
```

Both scripts accept `--limit N` for smoke testing on a handful of rows before committing to a full pass.

---

## 6. Output Layout

```
services/benchmarks/
├── results/                        # CSVs — gitignored, regenerated on each run
│   ├── rag_<ts>.csv
│   ├── llm_<ts>.csv
│   ├── llm_<ts>_rescored.csv       # Finding 4 audit artefact
│   └── llm_<ts>_mcq_rubric.csv     # Finding 5 audit artefact
├── reports/                        # Human-readable analysis — committed
├── methodologies/                  # What/why docs — committed
└── investigations/                 # One-off audit scripts
```

---

## 7. Reproducibility Notes

- Generation: `temperature=0.0`, `seed=7` across all Ollama calls.
- Judge: Gemini 2.5 Flash Lite, `temperature=0`, `max_workers=1`, batch size 5.
- RAGAS: version pinned in `services/requirements.txt` (currently 0.1.22).
- Each benchmark run produces a single timestamped CSV — no accidental overwrites.
- Model versions are pinned by Ollama tag (e.g. `gemma2:9b-instruct-q4_0`).
