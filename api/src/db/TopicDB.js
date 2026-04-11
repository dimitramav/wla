import Topic from "../models/Topic.js";

export class TopicDB {
    static async list() {
        // [{ slug, title, available }]
        return Topic.find({}, { _id: 0, slug: 1, title: 1, available: 1 }).lean();
    }

    static async get(slug) {
        return Topic.findOne({ slug }).lean();
    }

    static async upsert({ slug, title, available }) {
        await Topic.updateOne({ slug }, { $set: { slug, title, available } }, { upsert: true });
        return Topic.findOne({ slug }, { _id: 0, slug: 1, title: 1, available: 1 }).lean();
    }
}
