import fs from "node:fs";
import path from "node:path";
import yaml from "js-yaml";
import { RAG_CONTENT_DIR, KEYWORDS_YAML } from "./env.js";

export function loadLevelKeywords(topic, level) {
    const fp = path.join(RAG_CONTENT_DIR, `${topic}/${KEYWORDS_YAML}`);
    const yml = yaml.load(fs.readFileSync(fp, "utf8"));
    const all = yml?.[topic]?.[String(level)] || [];
    return Array.from(new Set(all)); // dedupe
}

export function computeWeaknessWeights(progressKeywordStats = [], level, lambda = 1.0) {
    // progressKeywordStats is the array you store per level:
    // [{ level, keyword, attempts, misses, miss_rate }]
    const stats = progressKeywordStats.filter(s => s.level === level);
    if (!stats.length) return []; // no weaknesses yet

    const rates = stats.map(s => s.miss_rate ?? 0);
    const min = Math.min(...rates), max = Math.max(...rates);
    const span = Math.max(1e-6, max - min);

    // Clamp weights to [1, 2]
    return stats.map(s => {
        const norm = (s.miss_rate - min) / span;
        const weight = Math.min(2, 1 + lambda * norm);
        return { key: s.keyword, weight: Number(weight.toFixed(3)) };
    });
}
