# Structure

## Directory Layout
```text
.
├── api/                   # Express backend (Node.js)
│   ├── src/
│   │   ├── db/            # Database wrappers/logic
│   │   ├── lib/           # Utility libraries (auth, env, etc.)
│   │   ├── models/        # Mongoose schemas/models
│   │   ├── routes/        # Express route definitions
│   │   ├── ragClient.js   # Bridging logic to FastAPI services
│   │   └── server.js      # Main API entry point
│   ├── package.json       # Node package configuration
│   └── package-lock.json  # Node dependency lock file
├── services/               # Specialized services (Python/FastAPI)
│   ├── api/               # FastAPI endpoints/models
│   │   ├── models/        # Python Pydantic models (implied)
│   │   └── routes/        # FastAPI route definitions (ingest, qg, summary)
│   ├── llm/               # LLM client and prompt templates
│   ├── rag/               # Vector search and document processing
│   ├── requirements.txt   # Python dependencies
│   ├── server.ipynb       # Jupyter notebook server entry
│   ├── setup.ipynb        # Setup/Installation script
│   └── test.ipynb         # Testing/Scratchpad
├── web/                   # Frontend React app (SPA)
│   ├── public/            # Static assets
│   ├── src/               # Application source code
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page-level components
│   │   ├── main.jsx       # React application entry point
│   │   └── index.css      # Core styles
│   ├── package.json       # Frontend package configuration
│   └── vite.config.js     # Vite build/dev server configuration
├── content/               # Application content (PDFs/metadata)
└── README.md              # Project documentation and setup guide
```

## Key Locations
- **API Entry**: `api/src/server.js` (Listening on port 3001)
- **Services Entry**: `services/server.ipynb` (Fires up FastAPI on port 8000 via Uvicorn)
- **Frontend Entry**: `web/src/main.jsx` (Development via Vite on port 5173)
- **Database Logic**: `api/src/db/` and `api/src/models/`
- **RAG Services**: `services/api/routes/` and `services/rag/`

## Naming Conventions
- **JavaScript (Node/React)**: CamelCase for files typically in `components/`, lowerCamelCase for utility files and routes.
- **Python (FastAPI)**: snake_case for files and directories (following PEP8).
- **Mongoose Models**: PascalCase (e.g., `Docset.js`, `User.js`).
