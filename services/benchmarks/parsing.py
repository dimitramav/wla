"""
LLM output parsing helpers for the benchmark pipelines.

Matches the production client.py JSON extraction logic so the benchmark
measures the same parser the production RAG service uses.
"""

import json
import re

REQUIRED_KEYS = {"text", "options", "correct", "why"}


def extract_json(text: str):
    """Extract first JSON object from LLM output (matches production client.py logic)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for m in re.finditer(r"[\{]", text):
        start = m.start()
        for end in range(len(text), start, -1):
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                continue
    return None


def validate_format(parsed) -> float:
    """Check JSON has required keys. Returns 1.0 (valid) or 0.0 (invalid)."""
    if not isinstance(parsed, dict):
        return 0.0
    if not REQUIRED_KEYS.issubset(parsed.keys()):
        return 0.0
    if not isinstance(parsed.get("options"), list) or len(parsed["options"]) != 4:
        return 0.0
    if parsed.get("correct") not in ("A", "B", "C", "D"):
        return 0.0
    return 1.0
