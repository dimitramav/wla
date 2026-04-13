/**
 *
 * This file defines routes for managing quizzes, including starting and submitting quizzes.
 *
 * Exposes:
 * - POST /api/:topic/quiz/start : Starts a new quiz for a user based on the specified topic and level.
 * - POST /api/:topic/quiz/submit : Submits quiz results, updates user progress, and tracks keyword statistics.
 *
 * Implementation notes:
 * - Validates input parameters such as `uid`, `level`, and `docsetHash`.
 * - Uses `qg` to generate quiz questions based on topic, level, and weak keywords.
 * - Updates user progress and keyword statistics upon quiz submission.
 */

import { Router } from "express";
import mongoose from "mongoose";
import { qg } from "../ragClient.js";
import { LEVELS } from "../lib/levels.js";
import { loadLevelKeywords } from "../lib/keywords.js";
import { QuizDB } from "../db/QuizDB.js";
import { ProgressDB } from "../db/ProgressDB.js";
import { computeWeakKeywords } from "../lib/keywords.js";
const router = Router({ mergeParams: true });

router.post("/:topic/quiz/start", async (req, res) => {
    try {
        const { topic } = req.params;
        const { level = 1, uid, docsetHash, weakFocusRatio } = req.body;
        //  basic input checks 
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
        //  keywords + per-level config
        const baseKeywords = loadLevelKeywords(topic, lvl);
        if (!baseKeywords.length) {
            return res.status(400).json({ error: { message: "No keywords for level" } });
        }
        let weakKeywords = await computeWeakKeywords(uid, topic, lvl);
        const cfg = LEVELS[lvl];
        // When no weak keywords (new user, no history), send all questions
        // through the strong (keyword-targeted) path to avoid untargeted chunks
        const effectiveWeakRatio = weakKeywords.length > 0
            ? (weakFocusRatio || 0.6)
            : 0.0;
        // call FastAPI /qg
        const payload = {
            hash: docsetHash,
            keywords: baseKeywords,
            mix: cfg.mix,
            seed: "default-seed",    // to be investigated
            difficulty_profile: cfg.difficulty_profile,
            weak_keywords: weakKeywords,
            weak_focus_ratio: effectiveWeakRatio,
        };
        const data = await qg(payload, topic);
        const qs = data?.questions || [];
        console.log("QG returned questions:", qs);
        if (!Array.isArray(qs) || qs.length !== 10) {
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
            weak_keywords: weakKeywords,
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
            // For MCQ, user answer is the full option string (e.g. "A) text") while
            // correct is just the letter (e.g. "A"), so compare first characters only
            const isCorrect = userAnswer != null && userAnswer.charAt(0) === q.correct.charAt(0);
            const kws = Array.isArray(q.keywords) ? q.keywords : [];
            for (const kw of kws) {
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
        await QuizDB.markSubmitted(quizId, correctCount, passed);
        return res.status(200).json({ success: true });


    } catch (e) {
        next(e);
    }
});

export default router;
