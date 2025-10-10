import mongoose from "mongoose";

const FileSchema = new mongoose.Schema({
    name: String,
    url: String,
    size: Number,
    mtime: Number,
}, { _id: false });

const DocsetSchema = new mongoose.Schema({
    topic: { type: String, index: true, required: true }, // topic slug
    hash: { type: String, unique: true, index: true, required: true },
    files: [FileSchema],
    summaryBullets: { type: [String], default: [] },
    model: String,
    promptHash: String,
}, { timestamps: true });

export default mongoose.model("Docset", DocsetSchema);
