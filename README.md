# Watch - Listen - Act

Adaptive teaching platform designed to train teachers on student mental health topics using RAG-powered quizzes with personalized difficulty scaling.

## Setup Guide (New Device)

Follow these steps to set up the project on a new machine:

### 1. Clone + Create Virtual Environment
```bash
git clone https://github.com/dimitramav/wla.git
cd wla
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python Dependencies
> [!IMPORTANT]
> **CPU PyTorch must be installed before requirements.** This prevents `sentence-transformers` from pulling GPU torch with CUDA dependencies that may not exist on your machine.

```bash
# Install CPU-only PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements
pip install -r services/requirements.txt
```

### 3. Install Node.js Dependencies
```bash
# Install API dependencies
cd api && npm install

# Install Web dependencies
cd ../web && npm install
```

## Quick Start (Recommended)

You can start all services at once using the provided scripts:

```bash
# Start all services (MongoDB, Express, FastAPI, Vite)
./scripts/start.sh

# Start services without the frontend
./scripts/start.sh --no-frontend

# Stop all services
./scripts/stop.sh
```

The `start.sh` script handles health checks and environment validation automatically. Logs for each service are piped to `/tmp/wla-express.log`, `/tmp/wla-fastapi.log`, and `/tmp/wla-vite.log`.

## Running the Application (Manual)

If you prefer to start services individually in their own terminals:

1.  **MongoDB**: `sudo systemctl start mongod`
2.  **Ollama**: Ensure Ollama is running and `mistral:7b-instruct-q4_0` is pulled.
3.  **Express API**: `cd api && npm run dev` (http://localhost:3001)
4.  **FastAPI RAG Service**: 
    -   `cd services && ../.venv/bin/python -m uvicorn api.main:app --factory --port 8000`
    -   *Or run all cells in `services/server.ipynb`*
5.  **React Web Frontend**: `cd web && npm run dev` (http://localhost:5173)

## RAG Retrieval Benchmarking

The project includes a benchmarking suite that evaluates retrieval quality across different embedding models, chunk sizes, and retrieval strategies.

### Prerequisites

- All Python dependencies installed (`pip install -r services/requirements.txt`)
- Ollama running with `mistral:7b-instruct-q4_0` pulled
- PDF corpus ingested for the target topic (e.g. `school_anxiety`)

### Running the benchmark

```bash
cd services
python -m benchmarks.rag_benchmark
```

This evaluates **12 configurations** (3 embedding models x 2 chunk sizes x 2 retrieval strategies) against 10 manually curated, corpus-grounded golden questions. Each configuration is scored using:

- **Cosine similarity** — how semantically similar the retrieved chunk is to the query
- **RAGAS context_precision** — whether the retrieved chunk actually contains the answer (LLM-judged)

Results are written to `services/benchmarks/results/` (120 rows). A detailed analysis is available in `services/benchmarks/RAG_BENCHMARK_REPORT.md`.

### Configurations tested

| Parameter | Values |
|-----------|--------|
| Embedding models | `all-MiniLM-L6-v2`, `all-mpnet-base-v2`, `bge-small-en-v1.5` |
| Chunk sizes | 512/50, 800/100 |
| Retrieval strategies | Dense (cosine similarity), Hybrid (BM25 + dense via RRF) |

### Runtime

The full benchmark takes **3–4 hours** on CPU, primarily due to RAGAS evaluation calls to Ollama. Progress is printed to stdout in real time when using the `-u` flag.

---

### External Dependencies
This project requires the following to be installed separately:
- **MongoDB**: [Installation Guide](https://www.mongodb.com/docs/manual/installation/)
- **Ollama**: [Download Ollama](https://ollama.com/)