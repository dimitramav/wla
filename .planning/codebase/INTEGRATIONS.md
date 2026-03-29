# Integrations

## Overview
The application follows a modular architecture where the Express API, React frontend, and FastAPI services communicate locally. It leverages local AI tools (Ollama) and a local Vector database (ChromaDB).

## Databases
- **MongoDB**: The primary application database for user data and metadata.
  - Connection: `mongodb://localhost:27017/wla` (local)
  - Tool: Mongoose
- **ChromaDB**: The vector store for the RAG (Retrieval Augmented Generation) pipeline.
  - Storage location: `rag/chroma`
  - Managed by FastAPI service.

## AI & LLM
- **LLM Engine**: [Ollama](https://ollama.com/) (running locally)
  - URL: `http://localhost:11434`
  - Model: `mistral:7b-instruct-q4_0`
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (running via FastAPI/ChromaDB).

## Service Communication
- **Frontend (Web) ➜ API (Express)**: REST via `http://localhost:3001`.
- **API (Express) ➜ RAG (FastAPI)**: REST via `http://localhost:8000`.
- **Web Origin**: `http://localhost:5173`.

## File Storage
- **Local Filesystem**: RAG content is stored in `../content`.
- **YAML**: Key-value metadata and keywords are managed in `keywords.yaml`.
