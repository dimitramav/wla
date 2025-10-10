import fetch from "node-fetch";
import fs from "fs";
import { RAG_BASE, DOCSET_FOLDER, RAG_DOCSETS_META } from "./lib/env.js";

export function readRagDocsetsJson() {
    const p = `../${DOCSET_FOLDER}/${RAG_DOCSETS_META}`;
    if (!fs.existsSync(p)) return {};
    return JSON.parse(fs.readFileSync(p, "utf-8"));
}

export async function getSummaryFromRag({ topic, hash }) {
    const url = new URL("/rag/summary", RAG_BASE);
    url.searchParams.set("topic", topic);
    // url.searchParams.set("hash", hash);
    console.log("Fetching summary from FastAPI:", url.toString());
    const r = await fetch(url.toString());
    if (!r.ok) throw new Error(`FastAPI ${r.status}`);
    const data = await r.json();
    return data;
}
