# Tech Stack

## Overview
This is a multi-service application consisting of a Node.js/Express API, a Python/FastAPI service layer (specializing in LLM and RAG), and a React-based frontend.

## Frontend
- **Framework**: [React 19](https://react.dev/)
- **Build Tool**: [Vite 7](https://vite.dev/)
- **Styling**: Sass, SASS (SCSS)
- **Libraries**:
  - `react-router-dom`: Client-side routing
  - `chart.js` & `react-chartjs-2`: Data visualization
  - `@react-pdf-viewer/core`: PDF viewer
  - `react-icons`: Icon library

## Backend (Express API)
- **Runtime**: [Node.js](https://nodejs.org/) (ES Modules)
- **Framework**: [Express 5](https://expressjs.com/)
- **Database**: [MongoDB](https://www.mongodb.com/) via [Mongoose 8](https://mongoosejs.com/)
- **Security**:
  - `jsonwebtoken`: Authentication
  - `bcrypt`: Password hashing
  - `cookie-parser`: Cookie-based session management

## Backend (FastAPI Services)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Vector Database**: [ChromaDB](https://www.trychroma.com/)
- **ML/LLM Support**:
  - `langchain-text-splitters`: Document processing
  - `sentence-transformers`: Embedding generation
  - `pypdf`: PDF processing
- **Data Serialization**: `orjson`
- **Settings Management**: `pydantic-settings`

## Environment & Configuration
- **Node.js**: `.env` used in both `api` and `web`.
- **Python**: `.env` used via `python-dotenv`.
- **Database**: MongoDB (likely local or Atlas depending on `.env`).
