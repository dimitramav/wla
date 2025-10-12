import fetch from "node-fetch";
import fs from "fs";
import { RAG_BASE, DOCSET_FOLDER, RAG_DOCSETS_META } from "./lib/env.js";

// --- Utility to read RAG docsets metadata ---
export function readRagDocsetsJson() {
    const p = `../${DOCSET_FOLDER}/${RAG_DOCSETS_META}`;
    if (!fs.existsSync(p)) return {};
    return JSON.parse(fs.readFileSync(p, "utf-8"));
}

// --- Fetch deterministic summary from FastAPI ---
export async function getSummaryFromRag({ topic, hash }) {
    const url = new URL("/rag/summary", RAG_BASE);
    url.searchParams.set("topic", topic);
    if (hash) url.searchParams.set("hash", hash);
    console.log("Fetching summary from FastAPI:", url.toString());

    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`FastAPI ${res.status}`);
    return res.json();
}

// --- Post question generation payload to FastAPI ---
export async function qg(payload) {
    const res = await fetch(`${RAG_BASE}/qg`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`QG failed: ${res.status} ${text}`);
    }

    return res.json();
}
