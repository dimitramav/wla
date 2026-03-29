/**
 *
 * This file provides utility functions to interact with the RAG (Retrieval-Augmented Generation) backend.
 *
 * Exposes:
 * - readRagDocsetsJson: Reads metadata about document sets from a JSON file.
 * - getSummaryFromRag: Fetches a summary for a topic from the FastAPI backend.
 * - qg: Sends a question generation payload to the FastAPI backend.
 *
 */

import fetch from "node-fetch";
import fs from "fs";
import { RAG_BASE, DOCSET_FOLDER, RAG_DOCSETS_META } from "./lib/env.js";

// Utility to read RAG docsets metadata
export function readRagDocsetsJson() {
    const p = `../${DOCSET_FOLDER}/${RAG_DOCSETS_META}`;
    if (!fs.existsSync(p)) return {};
    return JSON.parse(fs.readFileSync(p, "utf-8"));
}



/**
 * Fetches a summary for a topic from the FastAPI backend.
 *
 * Parameters:
 * - topic: The topic name for which the summary is requested.
 * - hash: (Optional) The hash of the document set.
 *
 * Returns:
 * - A JSON object containing the summary data.
 *
 * Throws:
 * - An error if the FastAPI response is not OK.
 */
export async function getSummaryFromRag({ topic, hash }) {
    const url = new URL("/rag/summary", RAG_BASE);
    url.searchParams.set("topic", topic);
    if (hash) url.searchParams.set("hash", hash);
    console.log("Fetching summary from FastAPI:", url.toString());

    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`FastAPI ${res.status}`);
    return res.json();
}

/**
 * Sends a question generation payload to the FastAPI backend.
 *
 * Parameters:
 * - payload: The question generation payload (includes keywords, difficulty, etc.).
 * - topic: The topic name for which the questions are generated.
 *
 * Returns:
 * - A JSON object containing the generated questions.
 *
 * Throws:
 * - An error if the FastAPI response is not OK.
 */
export async function qg(payload, topic) {
    const url = new URL("/qg", RAG_BASE);
    url.searchParams.set("topic", topic);
    const res = await fetch(url.toString(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        let detail = `QG failed: ${res.status}`;
        try {
            const body = await res.json();
            if (body.detail) detail = body.detail;
        } catch {
            // keep default
        }
        throw new Error(detail);
    }

    return res.json();
}
