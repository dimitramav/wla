import Quiz from "../models/Quiz.js";
import { QuizDB } from "../db/QuizDB.js";
import { loadLevelKeywords } from "./keywords.js";

function isLevelAligned(quiz, allowedKeywords) {
    const allowed = new Set(allowedKeywords);
    for (const q of quiz.questions || []) {
        for (const kw of q.keywords || []) {
            if (!allowed.has(kw)) return false;
        }
    }
    return true;
}

export async function tryDemoQuiz({ topic, level, docsetHash, uid, expectedCount, weakKeywords }) {
    if (process.env.DEMO_MODE !== "true") return null;

    const allowedKeywords = loadLevelKeywords(topic, level);

    const candidates = await Quiz.aggregate([
        {
            $match: {
                topic,
                docsetHash,
                level,
                seed: { $ne: "demo" },
                $expr: { $eq: [{ $size: "$questions" }, expectedCount] },
            },
        },
        { $sample: { size: 25 } },
    ]);

    const demoSource = candidates.find(c => isLevelAligned(c, allowedKeywords));

    if (!demoSource) {
        console.warn(`[demo-mode] no level-aligned cached quiz for ${topic} level ${level} — falling back to live generation`);
        return null;
    }

    const quiz = await QuizDB.createStarted({
        userId: uid,
        topic,
        docsetHash,
        level,
        seed: "demo",
        questions: demoSource.questions,
    });

    return {
        quizId: String(quiz._id),
        level,
        questions: demoSource.questions,
        weak_keywords: weakKeywords,
    };
}
