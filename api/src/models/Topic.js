import mongoose from "mongoose";

const TopicSchema = new mongoose.Schema({
    slug: { type: String, unique: true, index: true, required: true },
    title: { type: String, required: true },
}, { timestamps: true });

export default mongoose.model("Topic", TopicSchema);
