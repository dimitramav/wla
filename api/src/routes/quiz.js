// api/src/routes/quiz.js
import { Router } from "express";
import mongoose from "mongoose";
import { qg } from "../ragClient.js";
import { LEVELS } from "../lib/levels.js";
import { loadLevelKeywords } from "../lib/keywords.js";
import { QuizDB } from "../db/QuizDB.js";
import { ProgressDB } from "../db/ProgressDB.js";
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

router.post("/:topic/quiz/submit", async (req, res, next) => {
    try {
        const { topic } = req.params;
        const { quizId, correctCount, passed, userId, answers } = req.body;
        if (!quizId || !userId || typeof correctCount !== "number") {
            return res.status(400).json({ error: { message: "Missing required fields" } });
        }

        const quiz = await QuizDB.getById(quizId);
        if (!quiz) {
            return res.status(404).json({ error: { message: "Quiz not found" } });
        }
        // Ensure progress doc exists
        const prog = await ProgressDB.getOrCreate(userId, topic);
        const lvl = prog.perLevel.find(p => p.level === quiz.level);
        // Update stats
        lvl.attempts += 1;
        if (passed) lvl.passes += 1;
        lvl.lastScore = correctCount;
        lvl.lastAt = new Date();


        for (const q of quiz.questions) {
            const userAnswer = answers[q.id]; // direct lookup
            const isCorrect = userAnswer === q.correct; // simple strict compare
            const kws = Array.isArray(q.keywords) ? q.keywords : [];
            for (const kw of kws) {
                console.log(lvl.keywordStats);
                const statIndex = lvl.keywordStats.findIndex(s => s.keyword === kw);
                if (statIndex === -1) {
                    // If stat doesn't exist, create and push new one
                    const newStat = { keyword: kw, attempts: 1, misses: isCorrect ? 0 : 1, miss_rate: isCorrect ? 0 : 1 };
                    lvl.keywordStats.push(newStat);
                } else {
                    // If stat exists, modify it directly in the array
                    lvl.keywordStats[statIndex].attempts += 1;
                    if (!isCorrect) lvl.keywordStats[statIndex].misses += 1;
                    lvl.keywordStats[statIndex].miss_rate = lvl.keywordStats[statIndex].misses / lvl.keywordStats[statIndex].attempts;
                }
            }
        }

        // Unlock next level if passed
        if (passed && prog.unlockedLevel === quiz.level && quiz.level < 3) {
            prog.unlockedLevel = quiz.level + 1;
        }

        await prog.save();
        return res.status(200).json({ success: true });


    } catch (e) {
        next(e);
    }
});

export default router;
