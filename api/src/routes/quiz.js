import { qg } from "../ragClient.js";
import { LEVELS } from '../lib/levels.js';
import { loadLevelKeywords } from '../lib/keywords.js';
import Quiz from '../models/Quiz.js';
import Docset from '../models/Docset.js';
import Router from "express"
import mongoose from "mongoose";


const router = Router({ mergeParams: true });

router.post("/:topic/quiz/start", async (req, res) => {
    try {
        const { topic } = req.params;
        const level = Number(req.body.level || 1);

        if (![1, 2, 3].includes(level)) {
            return res.status(400).json({ error: { message: "Invalid level" } });
        }

        const docset = await Docset.findOne({ topic }).sort({ updatedAt: -1 }).lean();
        if (!docset?.hash) {
            return res.status(409).json({ error: { message: "Docset not ingested yet" } });
        }

        const baseKeywords = loadLevelKeywords(topic, level);
        if (!baseKeywords.length) {
            return res.status(400).json({ error: { message: "No keywords for level" } });
        }

        const cfg = LEVELS[level];

        const payload = {
            hash: docset.hash,
            level,
            keywords: baseKeywords,
            mix: cfg.mix,
            seed: "default-seed",
            difficulty_profile: cfg.difficulty_profile,
            weak_keywords: [],
        };

        const data = await qg(payload);
        const qs = data.questions;
        if (!Array.isArray(qs) || qs.length !== 15) {
            return res.status(502).json({ error: { message: "QG invalid response" } });
        }

        const quiz = await Quiz.create({
            userId: new mongoose.Types.ObjectId('000000000000000000000000'),
            topic,
            docsetHash: docset.hash,
            level,
            seed: "default-seed",
            status: "started",
            questions: qs, // includes 'correct'
        });

        // 🔥 Send full questions back, including 'correct'
        return res.json({
            quizId: String(quiz._id),
            level,
            questions: qs,
        });

    } catch (e) {
        console.error(e);
        return res.status(500).json({ error: { message: "Failed to start quiz" } });
    }
});

export default router;