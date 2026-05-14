# summary.py
#
# This file provides utilities for generating summaries for a specific topic and document set.
#
# Key Features:
# - Builds a stable context from vector store data.
# - Generates summary bullet points using an LLM.

from .vecstore import collection_for
from typing import List, Dict

MAX_CHARS = 4500   # keep context small for tiny CPU models
TOP_M     = 30     # take first 30 chunks in stable order

def build_stable_context(col, topic: str, docset_hash: str) -> str:
    # Retrieve metadata for the topic and document set from ChromaDB
    records = col.get(
        where={
            "$and": [
                {"topic": topic},
                {"docset_hash": docset_hash}
            ]
        },
        include=["documents", "metadatas"]
    )
    docs = records.get("documents", [])
    metas = records.get("metadatas", [])

    # Sort documents and metadata in a stable order
    ordered = sorted(zip(docs, metas), key=lambda x: (x[1].get("source",""), x[1].get("page", 0), x[1].get("chunk_idx", 0)))

    # Take the first TOP_M chunks and truncate to MAX_CHARS
    buf, total = [], 0
    for d, m in ordered[:TOP_M]:
        seg = f"[{m.get('source')} p{m.get('page')}:#{m.get('chunk_idx')}] {d}\n"
        if total + len(seg) > MAX_CHARS: break
        buf.append(seg); total += len(seg)
    return "".join(buf)

# Generate a summary for a topic and document set
#
# Parameters:
# - topic: The name of the topic.
# - docset_hash: The hash of the document set.
# - seed: An integer seed for deterministic generation (default: 7).
#
# Returns:
# - A dictionary containing the summary, prompt hash, and other metadata.
def summarize_topic(topic: str, docset_hash: str, seed: int = 7) -> Dict:
    from llm.prompts import SYSTEM_SUMMARY, USER_TEMPLATE
    from llm.client import generate_bullets, prompt_hash

    # Retrieve the ChromaDB collection for the topic
    col = collection_for(f"{topic}")

    # Build the stable context for the topic and document set
    ctx = build_stable_context(col, topic, docset_hash)

    # Format the user prompt for the LLM
    user = USER_TEMPLATE.format(topic=topic, docset_hash=docset_hash) + "\n\n" + ctx

    # Generate summary bullet points using the LLM
    bullets = generate_bullets(SYSTEM_SUMMARY, user, seed=seed, temperature=0.0)

    # Return the summary and metadata
    return {
        "topic": topic,
        "hash": docset_hash,
        "bullets": bullets,
        "promptHash": prompt_hash(user),
        "seed": seed,
    }
