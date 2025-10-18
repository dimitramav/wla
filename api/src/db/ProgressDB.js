import mongoose from "mongoose";
import Progress from "../models/Progress.js";

export class ProgressDB {
    //Get a user's progress for a topic
    static async get(userId, topic) {
        if (!mongoose.Types.ObjectId.isValid(userId)) return null;
        return await Progress.findOne({ userId, topic });
    }

    //Create default progress document if one doesn't exist
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


    //Save the given progress document
    static async save(doc) {
        return await doc.save();
    }


}           