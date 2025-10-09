import dotenv from 'dotenv';

dotenv.config({ path: '../.env' }); // Load .env from one level up

export const PORT = process.env.PORT || 3001;
export const WEB_ORIGIN = process.env.WEB_ORIGIN || 'http://127.0.0.1:5173';
export const MONGO_URL = process.env.MONGO_URL || 'mongodb://localhost:27017/wla';
export const RAG_BASE = process.env.RAG_BASE || 'http://localhost:8000';
export const JWT_SECRET = "aec27315ecce32ae570d24bdae1b11c71d39a244aa8a65090688697b1fe23cec5465a259f8e93305750660289a24b4b8b865480f1c7d6ce03a8ef771ed901ca8"
export const JWT_EXPIRES = "7d"
export const DOCSET_FOLDER = process.env.DOCSET_FOLDER || '/services';
export const RAG_DOCSETS_META = process.env.RAG_DOCSETS_META || 'rag/docsets.json';