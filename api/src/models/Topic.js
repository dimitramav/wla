import mongoose from "mongoose";

const TopicSchema = new mongoose.Schema({
    slug: { type: String, unique: true, index: true, required: true },
    title: { type: String, required: true },
    available: { type: Boolean, default: false },
}, { timestamps: true });

export default mongoose.model("Topic", TopicSchema);
