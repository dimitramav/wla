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

---

### External Dependencies
This project requires the following to be installed separately:
- **MongoDB**: [Installation Guide](https://www.mongodb.com/docs/manual/installation/)
- **Ollama**: [Download Ollama](https://ollama.com/)