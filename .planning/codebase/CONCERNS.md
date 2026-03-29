# Concerns

## Technical Debt
- **Automated Testing**: Complete lack of automated unit or integration tests for both the Express and FastAPI services.
- **Documentation**: No JSDoc or Python docstrings observed in the sampled entry points.
- **Service Management**: The Python FastAPI service is primarily managed via Jupyter Notebooks (`server.ipynb`), which may not be ideal for production-like environments or CI/CD pipelines.

## Security
- **Local Credentials**: While no hardcoded secrets were found, the `.env` at the root contains direct MongoDB and service URLs.
- **Input Validation**: The RAG ingestion logic is relatively complex and depends on external PDF processing (`pypdf`); this is a common area for edge-case bugs.

## Performance & Scalability
- **Local LLM**: Relying on local Ollama (`mistral:7b`) means performance is tied to the host machine's hardware.
- **Synchronous Execution**: Some database operations or LLM calls may block if not handled with proper worker queues (not observed in basic routes).

## Fragility
- **Inter-service Dependency**: The Express API fails if the FastAPI service is not already running on port 8000.
- **Vector Database**: ChromaDB is running in the local filesystem; there is no mention of persistent volume management or backup strategy in the current code.
