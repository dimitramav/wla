import { Router } from 'express';

const router = Router();

router.get('/', (_req, res) => {
  res.json({
    topics: [
      { slug: 'school_anxiety', title: 'School Anxiety' }
    ]
  });
});

export default router;