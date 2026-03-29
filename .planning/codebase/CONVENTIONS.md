# Conventions

## Code Style
- **JavaScript (Node.js/React)**:
  - **Modules**: Uses ES Modules (`import`/`export`) throughout the API and web project.
  - **Asynchronous Code**: Uses `async/wait` and standard promise handling (`.then()/.catch()`).
  - **Naming**: `camelCase` for variables and functions, `PascalCase` for React components and Mongoose models.
  - **Middleware**: Express uses standard middleware like `morgan` for logging and `cors` for cross-origin requests.
- **Python (FastAPI)**:
  - **Style**: Follows [PEP 8](https://peps.python.org/pep-0008/) naming conventions (snake_case).
  - **Structure**: Uses the Factory pattern (`create_app()`) to initialize the FastAPI application.
  - **Router**: Separation of routes into independent modules imported into the main application.

## Formatting & Linting
- **Web (React)**: ESLint is configured with the `eslint.config.js` file, focusing on React and Vite best practices.
- **Node.js**: No explicit linting config found in the root, but follows standard modern JS patterns.

## Error Handling
- **API (Express)**: Database connection failures result in a logged error and `process.exit(1)` to prevent running in an inconsistent state.
- **Health Checks**: Both internal services provide `/health` endpoints for monitoring.

## Design Patterns
- **API Gateway Pattern**: Express acts as a gatekeeper for the Python RAG services.
- **Model-Root-Router**: Separation of database schemas (`models/`), business logic (+lib), and HTTP endpoints (`routes/`).
