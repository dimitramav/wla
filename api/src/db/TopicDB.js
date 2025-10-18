import Topic from "../models/Topic.js";

export class TopicDB {
    static async list() {
        // [{ slug, title }]
        return Topic.find({}, { _id: 0, slug: 1, title: 1 }).lean();
    }

    static async get(slug) {
        return Topic.findOne({ slug }).lean();
    }

    static async upsert({ slug, title }) {
        await Topic.updateOne({ slug }, { $set: { slug, title } }, { upsert: true });
        return Topic.findOne({ slug }, { _id: 0, slug: 1, title: 1 }).lean();
    }
}
