import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional

from .settings import DOCLING_CACHE_DIR

_MIN_ELEMENT_CHARS = 10
_PARTIAL_MIN_LEN = 30
_PARTIAL_MIN_RATIO = 0.5
_ws_re = re.compile(r"\s+")
_alnum_re = re.compile(r"[^a-z0-9\s]")


def _normalize(text: str) -> str:
    text = text.lower()
    text = _alnum_re.sub(" ", text)
    text = _ws_re.sub(" ", text).strip()
    return text


def _load_cache(topic: str, doc: str) -> Optional[Dict[str, Any]]:
    path = DOCLING_CACHE_DIR / topic / f"{doc}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def find_spans(topic: str, doc: str, chunk_text: str) -> List[Dict[str, Any]]:
    """Return docling elements that overlap with chunk_text.

    The chunk-vs-element comparison runs on normalized text (lowercased,
    non-alphanumeric stripped, whitespace collapsed) so ligatures, smart
    quotes, and hyphenation across lines don't break matches the way pdf.js
    literal search does.
    """
    cache = _load_cache(topic, doc)
    if not cache:
        return []
    chunk_norm = _normalize(chunk_text)
    if not chunk_norm:
        return []

    hits: List[Dict[str, Any]] = []
    for el in cache.get("elements", []):
        el_text = el.get("text", "")
        el_norm = _normalize(el_text)
        if len(el_norm) < _MIN_ELEMENT_CHARS:
            continue

        score = 0.0
        if el_norm in chunk_norm:
            score = 1.0
        elif chunk_norm in el_norm:
            score = 1.0
        else:
            match = SequenceMatcher(None, chunk_norm, el_norm, autojunk=False).find_longest_match(
                0, len(chunk_norm), 0, len(el_norm)
            )
            if match.size >= _PARTIAL_MIN_LEN and match.size / len(el_norm) >= _PARTIAL_MIN_RATIO:
                score = round(match.size / len(el_norm), 4)

        if score > 0:
            hits.append({
                "page": el["page"],
                "bbox": el["bbox"],
                "score": score,
            })

    hits.sort(key=lambda h: (h["page"], h["bbox"][1]))
    return hits
