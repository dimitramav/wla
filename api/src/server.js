import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import path from 'path';
import { fileURLToPath } from 'url';
import { PORT, WEB_ORIGIN } from './lib/env.js';

import lessonsRouter from './routes/lessons.js';
import docsRouter from './routes/docs.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

app.use(morgan('dev'));
app.use(express.json());
app.use(cors({
  origin: WEB_ORIGIN,
  credentials: true
}));

// Static PDFs: /pdfs/:lesson/* -> ../content/:lesson/*
const pdfsRoot = path.resolve(__dirname, '../../content');
app.use('/pdfs', express.static(pdfsRoot, {
  setHeaders(res) {
    // allow range requests (pdf streaming)
    res.setHeader('Accept-Ranges', 'bytes');
  }
}));

// API routes
app.use('/api/lessons', lessonsRouter);
app.use('/api', docsRouter); // exposes GET /api/:lesson/docs

app.get('/health', (_req, res) => res.json({ ok: true, service: 'express' }));

app.listen(PORT, () => {
  console.log(`API listening on http://localhost:${PORT}`);
  console.log(`Static PDFs served from ${pdfsRoot} at /pdfs`);
});
