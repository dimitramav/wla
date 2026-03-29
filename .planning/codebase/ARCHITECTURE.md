# Architecture

## System Design
The application is structured as a three-tier system:
1.  **Frontend**: A React SPA that handles the user interface and presentation.
2.  **API Gateway (Express)**: Orchestrates business logic, manages user state, authentication, and acts as a gateway to the RAG services.
3.  **RAG Service (FastAPI)**: A specialized Python microservice for heavy AI, LLM, and Vector storage tasks.

## Data Flow
1.  **User Interaction**: Users interact with the React frontend (`web`).
2.  **Authentication & CRUD**: Frontend sends requests to the Express API (`api`).
3.  **AI & Knowledge Requests**: Express API calls the FastAPI service (`services`) via the `ragClient.js` when AI-related tasks (like quiz generation, document ingestion, or summarization) are needed.
4.  **Vector Processing**: The FastAPI service uses the local ChromaDB and Ollama LLM to process documents and generate responses.

## Module Boundaries
- **API (Node.js)**:
  - `db/` and `models/`: Core domain entities (Users, Topics, Progress, etc.).
  - `routes/`: Business capabilities exposed as RESTful endpoints.
  - `ragClient.js`: A specialized bridge to the Python backend.
- **Services (Python)**:
  - `api/routes/`: Capabilities like `qg` (Question Generation), `ingest`, and `summary`.
  - `llm/`: Direct interaction with the LLM (Ollama).
  - `rag/`: Document ingestion and retrieval pipeline.

## Key Patterns
- **Database Wrapper**: `api/src/db` uses specialized database wrappers (like `DocsetDB.js`) to provide access to Mongoose models.
- **RESTful API**: Both the Express and FastAPI layers follow RESTful conventions for internal and external communication.
- **RAG Pattern**: The FastAPI layer implements the classic Retrieval-Augmented Generation pattern (Ingest ➜ Embed ➜ Store ➜ Query ➜ LLM ➜ Output).
