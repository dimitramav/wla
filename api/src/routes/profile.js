import express from "express";
import { ProgressDB } from "../db/ProgressDB.js";

const router = express.Router();

router.post("/:topic/profile", async (req, res, next) => {
    try {
        const { topic } = req.params;
        const { userId } = req.body;

        if (!userId) {
            return res.status(400).json({ error: "Missing userId" });
        }

        // Ensures a progress document always exists
        const prog = await ProgressDB.getOrCreate(userId, topic);

        return res.json({
            unlockedLevel: prog.unlockedLevel,
            perLevel: prog.perLevel
        });

    } catch (e) {
        next(e);
    }
});

export default router;