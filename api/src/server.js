import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import path from 'path';
import { fileURLToPath } from 'url';
import { PORT } from './lib/env.js'; // Removed WEB_ORIGIN

import lessonsRouter from './routes/lessons.js';
import docsRouter from './routes/docs.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

const allowedOrigins = [
  'http://localhost:5173',
  'http://127.0.0.1:5173'
];

app.use(morgan('dev'));
app.use(express.json());

app.use(cors({
  origin: function (origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error(`CORS not allowed for origin: ${origin}`));
    }
  },
  credentials: true
}));

// Serve static PDFs
const pdfsRoot = path.resolve(__dirname, '../../content');
app.use('/pdfs', express.static(pdfsRoot, {
  setHeaders(res) {
    res.setHeader('Accept-Ranges', 'bytes');
  }
}));

// API routes
app.use('/api/lessons', lessonsRouter);
app.use('/api', docsRouter);
app.get('/health', (_req, res) => res.json({ ok: true, service: 'express' }));

app.listen(PORT, () => {
  console.log(`API listening on http://localhost:${PORT}`);
  console.log(`Static PDFs served from ${pdfsRoot} at /pdfs`);
});
