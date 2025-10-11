import mongoose from "mongoose";

const SourceSpan = new mongoose.Schema({
    doc: String,
    page_from: Number,
    page_to: Number,
    chunk_id: String,
}, { _id: false });

const Question = new mongoose.Schema({
    id: String,
    kind: { type: String, enum: ["mcq", "yesno"] },
    text: String,
    options: [String],
    correct: String,          // stored server-side only
    keywords: [String],
    source_spans: [SourceSpan],
}, { _id: false });

const QuizSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, index: true, required: true },
    topic: { type: String, index: true, required: true },
    docsetHash: { type: String, index: true, required: true },
    level: { type: Number, enum: [1, 2, 3], required: true },
    seed: { type: String },
    status: { type: String, enum: ["started", "submitted"], default: "started" },
    questions: [Question],
    answers: { type: [{ qid: String, answer: String }], default: [] },
    score: Number,
    passed: Boolean,
    startedAt: { type: Date, default: () => new Date() },
    submittedAt: Date,
}, { timestamps: true });

export default mongoose.model("Quiz", QuizSchema);
