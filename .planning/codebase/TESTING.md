# Testing

## Overview
The codebase currently relies on manual testing and interactive notebooks rather than formal unit/integration test suites.

## Existing Test Resources
- **Services (FastAPI/Python)**:
  - `services/test.ipynb`: A Jupyter notebook used for testing RAG, ingestion, and query generation logic.
  - `services/api/routes/health.py`: A simple health check endpoint.
- **Express API (Node.js)**:
  - `/health` endpoint for runtime health signals.
- **Frontend (Web)**:
  - ESLint for static code analysis (`npm run lint`).

## Testing Gaps
- **Automated Tests**: No formal test runners like `Jest`, `Mocha`, or `Pytest` are configured.
- **CI/CD**: No CI configuration (GitHub Actions, etc.) detected.
- **Integration Tests**: Communication between Express and FastAPI is tested manually via `ragClient.js`.

## Future Testing Goals
1.  **Unit Tests**: Implement Pytest for the FastAPI RAG logic and Jest for Express business logic.
2.  **Mocking Inter-service Communication**: Add mocks for the FastAPI services in Express API tests.
3.  **UI Testing**: Implement Playwright or Cypress for the React frontend.
