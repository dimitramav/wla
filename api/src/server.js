import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import cookieParser from 'cookie-parser';
import path from 'path';
import { fileURLToPath } from 'url';
import { PORT } from './lib/env.js';

import topicsRouter from './routes/topics.js';
import docsRouter from './routes/docs.js';
import authRouter from './routes/auth.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

const allowedOrigins = [
  'http://localhost:5173',
];

app.use(morgan('dev'));
app.use(express.json());
app.use(cookieParser());

app.use(cors({
  origin(origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) callback(null, true);
    else callback(new Error(`CORS not allowed for origin: ${origin}`));
  },
  credentials: true
}));

//serve static PDFs
const pdfsRoot = path.resolve(__dirname, '../../content');
app.use('/pdfs', express.static(pdfsRoot, {
  setHeaders(res) { res.setHeader('Accept-Ranges', 'bytes'); }
}));

//auth
app.use('/api/auth', authRouter);

// API routes (leave open now; you can protect with authRequired later)
// app.use('/api/topics', authRequired, topicsRouter);
app.use('/api/topics', topicsRouter);
app.use('/api', docsRouter);

app.get('/health', (_req, res) => res.json({ ok: true, service: 'express' }));

app.listen(PORT, () => {
  console.log(`API listening on http://localhost:${PORT}`);
  console.log(`Static PDFs served from ${pdfsRoot} at /pdfs`);
});
