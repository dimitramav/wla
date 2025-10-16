import mongoose from "mongoose";

const KeywordStat = new mongoose.Schema({
    keyword: { type: String, index: true },
    attempts: { type: Number, default: 0 },
    misses: { type: Number, default: 0 },
    miss_rate: { type: Number, default: 0 }, // misses/attempts
    ema_miss: { type: Number, default: 0 }, // optional smoothing [0..1]
}, { _id: false });

const LevelBlock = new mongoose.Schema({
    level: { type: Number, enum: [1, 2, 3], required: true },
    attempts: { type: Number, default: 0 },
    passes: { type: Number, default: 0 },
    lastScore: { type: Number, default: 0 },
    lastAt: { type: Date },
    keywordStats: { type: [KeywordStat], default: [] }
}, { _id: false });

const ProgressSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, index: true, required: true },
    topic: { type: String, index: true, required: true }, // slug
    unlockedLevel: { type: Number, enum: [1, 2, 3], default: 1 },
    perLevel: {
        type: [LevelBlock],
        default: [{ level: 1 }, { level: 2 }, { level: 3 }]
    },

}, {
    timestamps: true,
    collection: "progress"
});

ProgressSchema.index({ userId: 1, topic: 1 }, { unique: true });

export default mongoose.model("Progress", ProgressSchema);
