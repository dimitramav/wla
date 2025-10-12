// api/src/routes/quiz.js
import { Router } from "express";
import mongoose from "mongoose";
import { qg } from "../ragClient.js";
import { LEVELS } from "../lib/levels.js";
import { loadLevelKeywords } from "../lib/keywords.js";
import { QuizDB } from "../db/QuizDB.js";

const router = Router({ mergeParams: true });

router.post("/:topic/quiz/start", async (req, res) => {
    try {
        const { topic } = req.params;
        const { level = 1, uid, docsetHash } = req.body;
        // — basic input checks —
        const lvl = Number(level);
        if (![1, 2, 3].includes(lvl)) {
            return res.status(400).json({ error: { message: "Invalid level" } });
        }
        if (!uid || !mongoose.Types.ObjectId.isValid(uid)) {
            return res.status(400).json({ error: { message: "Missing or invalid uid" } });
        }
        if (!docsetHash) {
            return res.status(400).json({ error: { message: "Missing or invalid docset" } });
        }


        // — keywords + per-level config —
        const baseKeywords = loadLevelKeywords(topic, lvl);
        if (!baseKeywords.length) {
            return res.status(400).json({ error: { message: "No keywords for level" } });
        }
        const cfg = LEVELS[lvl];

        // — call FastAPI /qg —
        const payload = {
            hash: docsetHash,
            level: lvl,
            keywords: baseKeywords,
            mix: cfg.mix,
            seed: "default-seed",                     // swap to user's seed later if you wish
            difficulty_profile: cfg.difficulty_profile,
            weak_keywords: [],                        // add from Progress later (Day 10)
        };
        const data = await qg(payload);
        const qs = data?.questions || [];
        if (!Array.isArray(qs) || qs.length !== 15) {
            return res.status(502).json({ error: { message: "QG invalid response" } });
        }

        const quiz = await QuizDB.createStarted({
            userId: uid,
            topic,
            docsetHash: docsetHash,
            level: lvl,
            seed: "default-seed",
            questions: qs,
        });

        return res.json({
            quizId: String(quiz._id),
            level: lvl,
            questions: qs, // includes 'correct'
        });
    } catch (e) {
        console.error(e);
        return res.status(500).json({ error: { message: "Failed to start quiz" } });
    }
});

export default router;
