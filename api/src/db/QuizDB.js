import mongoose from "mongoose";
import Quiz from "../models/Quiz.js";

export class QuizDB {
    /**
     * Create a "started" quiz snapshot
     */
    static async createStarted({ userId, topic, docsetHash, level, seed, questions }) {
        const quiz = await Quiz.create({
            userId: userId,
            topic,
            docsetHash,
            level,
            seed,
            status: "started",
            questions,
            startedAt: new Date(),
        });
        return quiz;
    }

    /**
     * Get quiz by id
     */
    static async getById(quizId) {
        if (!mongoose.Types.ObjectId.isValid(quizId)) return null;
        return await Quiz.findById(quizId).lean();
    }
}
