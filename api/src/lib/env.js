import dotenv from 'dotenv';
dotenv.config();

export const PORT = process.env.PORT || 3001;
export const WEB_ORIGIN = process.env.WEB_ORIGIN || 'http://127.0.0.1:5173';

export const MONGO_URL = process.env.MONGO_URL || 'mongodb://localhost:27017/wla';
export const RAG_BASE = process.env.RAG_BASE || 'http://localhost:8000';
