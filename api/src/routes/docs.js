import { Router } from 'express';
import path from 'path';
import fs from 'fs';

const router = Router();

/**
 * GET /api/:topic/docs
 * Lists PDFs from content/:topic
 **/
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
