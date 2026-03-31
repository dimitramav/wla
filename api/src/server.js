/**
 *
 * This file initializes and configures the Express.js server for the API.
 *
 * Key Features:
 * - Connects to MongoDB using `connectDB`.
 * - Configures middleware for logging, JSON parsing, cookies, and CORS.
 * - Serves static PDF files from the `content` directory.
 * - Defines API routes for topics, documents, quizzes, profiles, and progress.
 * - Includes a health check endpoint.
 */

import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import cookieParser from 'cookie-parser';
import path from 'path';
import { fileURLToPath } from 'url';
import { PORT } from './lib/env.js';
import { connectDB } from './db/connection.js';

import topicsRouter from './routes/topics.js';
import docsRouter from './routes/docs.js';
import authRouter from './routes/auth.js';
import quizRouter from './routes/quiz.js';
import profileRouter from './routes/profile.js';
import progressRouter from './routes/progress.js';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();


const allowedOrigins = [
  'http://localhost:5173',
  'http://127.0.0.1:5173',
];

app.use(morgan('dev')); //logs http requests
app.use(express.json()); //parse incoming json
app.use(cookieParser()); //enable cookies

app.use(cors({
  origin(origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) callback(null, true);
    else callback(new Error(`CORS not allowed for origin: ${origin}`));
  },
  credentials: true
}));

// Serve static PDFs from content directory
const pdfsRoot = path.resolve(__dirname, '../../content');
app.use('/pdfs', express.static(pdfsRoot, {
  setHeaders(res) { res.setHeader('Accept-Ranges', 'bytes'); }
}));

app.use('/api/auth', authRouter);


app.use('/api/topics', topicsRouter);
app.use('/api', docsRouter);
app.use("/api", quizRouter);
app.use("/api", profileRouter);
app.use("/api", progressRouter);

app.get('/health', (_req, res) => res.json({ ok: true, service: 'express' }));

// Connect to DB then start the server
connectDB()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`API listening on http://localhost:${PORT}`);
      console.log(`Static PDFs served from ${pdfsRoot} at /pdfs`);
    });
  })
  .catch(err => {
    console.error('Failed to connect to MongoDB:', err);
    process.exit(1);
  });
