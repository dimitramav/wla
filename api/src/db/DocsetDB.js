// server/db/DocsetDB.js
import Docset from "../models/Docset.js";

export class DocsetDB {
    /** Return newest docset by updatedAt for a topic */
    static async getLatest(topic) {
        const doc = await Docset.findOne({ topic }).sort({ updatedAt: -1 }).lean();
        if (!doc) {
            return null;
        }
        return doc;
    }

    /** Return specific docset by topic+hash */
    static async getByHash(topic, hash) {
        const doc = await Docset.findOne({ topic, hash }).lean();
        if (!doc) {
            return null;
        }
        return doc;
    }

    /** Create/update docset shell (no bullets yet) */
    static async upsertShell({ topic, hash, files = [] }) {
        await Docset.updateOne(
            { topic, hash },
            { $set: { topic, hash, files } },
            { upsert: true }
        );
        return Docset.findOne({ topic, hash }).lean();
    }

    /** Persist summary result for topic+hash */
    static async saveSummary({ topic, hash, bullets, model, promptHash, files }) {
        await Docset.updateOne(
            { topic, hash },
            { $set: { summaryBullets: bullets || [], model, promptHash, files: files || [] } },
            { upsert: true }
        );
        return Docset.findOne({ topic, hash }).lean();
    }
}
