import { Router } from 'express';
import path from 'path';
import fs from 'fs';

const router = Router();

/**
 * GET /api/:lesson/docs
 * Lists PDFs from content/:lesson
 **/
router.get('/:lesson/docs', (req, res) => {
  const { lesson } = req.params;
  const base = path.resolve(process.cwd(), '../content', lesson);
  if (!fs.existsSync(base)) {
    return res.json({ docs: [] });
  }
  const files = fs.readdirSync(base)
    .filter(f => f.toLowerCase().endsWith('.pdf'))
    .map(title => ({
      title,
      url: `/pdfs/${lesson}/${title}`
    }));
  res.json({ docs: files });
});

export default router;
