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

### 4. Environment Configuration
The `web/.env` file is gitignored and must be created manually:
```bash
echo "VITE_API_BASE=http://localhost:3001" > web/.env
```

## Running the Application

Start each service in its own terminal in the following order:

1.  **MongoDB**: `sudo systemctl start mongod` (Ensure it's running: `sudo systemctl status mongod`)
2.  **Ollama**: Ensure Ollama is running and the model `mistral:7b-instruct-q4_0` is pulled.
3.  **Express API**: `cd api && npm run dev` (Listening on http://localhost:3001)
4.  **FastAPI RAG Service**: 
    -   Open `services/server.ipynb` and run all cells (Uvicorn running on http://localhost:8000)
    -   *Note: On first run, you may need to run cells in `services/setup.ipynb` if not done via CLI.*
5.  **React Web Frontend**: `cd web && npm run dev` (Access at http://localhost:5173)

---

### External Dependencies
This project requires the following to be installed separately:
- **MongoDB**: [Installation Guide](https://www.mongodb.com/docs/manual/installation/)
- **Ollama**: [Download Ollama](https://ollama.com/)