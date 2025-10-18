import fs from "node:fs";
import path from "node:path";
import yaml from "js-yaml";
import { RAG_CONTENT_DIR, KEYWORDS_YAML } from "./env.js";
import { ProgressDB } from "../db/ProgressDB.js";

export function loadLevelKeywords(topic, level) {
    const fp = path.join(RAG_CONTENT_DIR, `${topic}/${KEYWORDS_YAML}`);
    const yml = yaml.load(fs.readFileSync(fp, "utf8"));
    const all = yml?.[topic]?.[String(level)] || [];
    return Array.from(new Set(all)); // dedupe
}

export async function computeWeakKeywords(uid, topic, lvl) {
    let weakKeywords = [];
    const prog = await ProgressDB.get(uid, topic);
    if (prog) {
        const lvlData = prog.perLevel.find(l => l.level === lvl);
        if (lvlData && Array.isArray(lvlData.keywordStats)) {
            // sort by miss_rate descending, filter reasonable thresholds
            const sorted = [...lvlData.keywordStats]
                .sort((a, b) => b.miss_rate - a.miss_rate);

            // take top 3 weak keywords for now
            weakKeywords = sorted.length > 0
                ? sorted.slice(0, 3).map(k => k.keyword)
                : [];
        }
    }
    return weakKeywords;
}
