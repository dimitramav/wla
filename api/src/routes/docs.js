/**
 * docs.js
 *
 * This file defines routes for serving PDFs for a given topic.
 *
 * Exposes:
 * - GET /api/:topic/docs : Lists all PDF files in the `content/:topic` directory.
 * * - Constructs URLs for each PDF file to be served via `/pdfs/:topic/:filename`.
 * * - Returns an empty list if the topic directory does not exist.
 */

import { Router } from 'express';
import path from 'path';
import fs from 'fs';

const router = Router();
router.get('/:topic/docs', (req, res) => {
  const { topic } = req.params;
  const base = path.resolve(process.cwd(), '../content', topic);
  if (!fs.existsSync(base)) {
    return res.json({ docs: [] });
  }
  const files = fs.readdirSync(base)
    .filter(f => f.toLowerCase().endsWith('.pdf'))
    .map(title => ({
      title,
      url: `/pdfs/${topic}/${title}`
    }));
  res.json({ docs: files });
});

export default router;
