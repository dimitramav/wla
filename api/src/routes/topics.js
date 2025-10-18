/**
 *
 * This file defines routes for managing topics and their summaries.
 *
 * Exposes:
 * - GET /api/topics : Retrieves a list of all topics.
 * - GET /api/topics/:slug/summary : Retrieves or generates a summary for a specific topic.
 *
 * Implementation notes:
 * - Reads `rag/docsets.json` to determine the latest document set hash for a topic.
 * - Caches summaries in `DocsetDB` to avoid redundant computations.
 * - Calls FastAPI to generate summaries when not cached.
 */

import { Router } from "express";
import { TopicDB } from "../db/TopicDB.js";
import { DocsetDB } from "../db/DocsetDB.js";
import { readRagDocsetsJson, getSummaryFromRag } from "../ragClient.js";

const router = Router();


router.get("/", async (_req, res) => {
  try {
    const topics = await TopicDB.list();
    res.json({ topics });
  } catch (e) {
    console.error("Error loading topics:", e);
    res.status(500).json({ error: "topics_load_failed" });
  }
});


router.get("/:slug/summary", async (req, res) => {
  const topic = req.params.slug;

  try {
    // 1) Lookup latest hash from rag/docsets.json
    const meta = readRagDocsetsJson(); // { [topic]: { hash, files[] } }
    const live = meta[topic];
    if (!live?.hash) return res.status(404).json({ error: "docset_not_found" });
    const latestHash = live.hash;

    // 2) Check cache for this exact version
    let ds = await DocsetDB.getByHash(topic, latestHash);
    console.log("Found docset:", ds);
    if (ds?.summaryBullets?.length) {
      return res.json({
        topic,
        bullets: ds.summaryBullets,
        model: ds.model || null,
        promptHash: ds.promptHash || null,
        hash: latestHash,
        source: "cache",
      });
    }

    // 3) Ensure a shell doc exists (for audit/UI)
    if (!ds) {
      ds = await DocsetDB.upsertShell({ topic, hash: latestHash, files: live.files || [] });
    }

    // 4) Compute via FastAPI for this {topic, latestHash}
    console.log(`RAG summary miss; fetching fresh for topic=${topic} hash=${latestHash}`);
    const out = await getSummaryFromRag({ topic: topic, hash: latestHash });
    const updated = await DocsetDB.saveSummary({
      topic,
      hash: latestHash,
      bullets: out.bullets || [],
      promptHash: out.promptHash,
      files: ds.files || live.files || [],
    });
    return res.json({
      topic,
      hash: latestHash,
      bullets: updated.summaryBullets,
      promptHash: updated.promptHash || null,
    });
  } catch (e) {
    console.error("summary route failed:", e);
    res.status(502).json({ error: "rag_summary_failed" });
  }
});

export default router;
