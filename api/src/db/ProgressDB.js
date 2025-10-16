import mongoose from "mongoose";
import Progress from "../models/Progress.js";

export class ProgressDB {
    /**
     * Get a user's progress for a topic
     * @param {String|ObjectId} userId 
     * @param {String} topic 
     * @returns Progress document or null
     */
    static async get(userId, topic) {
        if (!mongoose.Types.ObjectId.isValid(userId)) return null;
        return await Progress.findOne({ userId, topic });
    }

    /**
     * Create default progress document if one doesn't exist
     * @param {String|ObjectId} userId 
     * @param {String} topic 
     * @returns New or existing Progress document
     */
    static async get(userId, topic) {
        if (!mongoose.Types.ObjectId.isValid(userId)) return null;
        return await Progress.findOne({ userId, topic }).lean();
    }

    static async getOrCreate(userId, topic) {
        if (!mongoose.Types.ObjectId.isValid(userId)) return null;

        let prog = await Progress.findOne({ userId, topic });
        if (!prog) {
            prog = new Progress({
                userId,
                topic,
                unlockedLevel: 1,
                perLevel: [
                    { level: 1, attempts: 0, passes: 0, lastScore: 0, lastAt: null, keywordStats: [] },
                    { level: 2, attempts: 0, passes: 0, lastScore: 0, lastAt: null, keywordStats: [] },
                    { level: 3, attempts: 0, passes: 0, lastScore: 0, lastAt: null, keywordStats: [] }
                ]
            });
            await prog.save();
        }
        return prog;
    }

    /**
     * Save the given progress document
     */
    static async save(doc) {
        return await doc.save();
    }
}
