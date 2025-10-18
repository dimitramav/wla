/**
 *
 * This file defines routes for managing and retrieving user progress data for specific topics.
 *
 * Exposes:
 * - POST /api/topics/:topic/progress : Ensures a progress document exists for a user and retrieves their progress.
 */

import { Router } from "express";
import mongoose from "mongoose";
import { ProgressDB } from "../db/ProgressDB.js";

const router = Router();

router.post("/:topic/progress", async (req, res) => {
    try {
        const topic = req.params.topic;
        const { userId } = req.body || {};

        // Validate userId
        if (!userId || !mongoose.Types.ObjectId.isValid(userId)) {
            return res.status(400).json({ error: { code: "bad_request", message: "Missing or invalid userId" } });
        }

        // Ensure a progress doc exists, then return a compact view
        const prog = await ProgressDB.getOrCreate(userId, topic);

        const perLevel = (prog.perLevel || [])
            .map(l => ({
                level: l.level,
                attempts: l.attempts || 0,
                passes: l.passes || 0,
                lastScore: l.lastScore || 0,
                lastAt: l.lastAt || null,
                keywordStats: l.keywordStats || [],
            }))
            .sort((a, b) => a.level - b.level);

        return res.json({
            topic,
            userId: String(prog.userId),
            unlockedLevel: prog.unlockedLevel,
            perLevel,
        });
    } catch (e) {
        console.error("progress route failed:", e);
        return res.status(500).json({ error: { code: "progress_failed", message: "Failed to load/create progress" } });
    }
});

export default router;
