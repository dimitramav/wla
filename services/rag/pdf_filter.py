# This file provides utilities for extracting text from documents (PDF, MD, TXT).
#
# Key Features:
# - Uses Docling (IBM) for ML-based PDF document understanding.
# - Handles two-column layouts, tables, and academic paper structure.
# - Reads .md and .txt files directly without conversion.
#
# Dependencies:
# - Docling for PDF parsing and structure extraction.

import re
import logging
from pathlib import Path
from typing import Dict, Any

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)

# Lazy-initialized converter (heavy object — load once)
_converter = None

def _get_converter() -> DocumentConverter:
    global _converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter

# Regex patterns to trim references/bibliography from extracted text
_END_PATTERNS = [
    r"^#+\s*References\b",
    r"^#+\s*Bibliography\b",
    r"^References$",
    r"^Bibliography$",
]


def _trim_references(text: str) -> str:
    """Remove References/Bibliography section and everything after it."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        for pat in _END_PATTERNS:
            if re.search(pat, line.strip(), flags=re.IGNORECASE):
                return "\n".join(lines[:i]).strip()
    return text


# Filter and extract text from a document (PDF, MD, or TXT)
def filter_document(path: Path) -> Dict[str, Any]:
    # For plain text and markdown files, read directly
    if path.suffix.lower() in (".md", ".txt"):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except Exception:
            text = ""
        return {
            "text": text,
            "notes": "text_file",
            "skipped_pages": [],
            "preview": text[:500],
        }

    # PDF path — use Docling for ML-based extraction
    try:
        converter = _get_converter()
        result = converter.convert(str(path))
        md_text = result.document.export_to_markdown()

        # Trim references section (not useful for question generation)
        text = _trim_references(md_text).strip()

        return {
            "text": text,
            "notes": "docling",
            "skipped_pages": [],
            "preview": text[:500],
        }
    except Exception as e:
        logger.error(f"Docling failed for {path.name}: {e}")
        return {
            "text": "",
            "notes": f"docling_error: {e}",
            "skipped_pages": [],
            "preview": "",
        }


# Backward-compatible alias
filter_research_pdf = filter_document
