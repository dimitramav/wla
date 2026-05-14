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

# Sections that are not useful for question generation
_SKIP_SECTION_PATTERNS = [
    r"^#+\s*(?:Acknowledgements?|Funding|Conflicts?\s+of\s+Interest|"
    r"Author\s+Contributions?|Data\s+Availability|Abbreviations|"
    r"Supplementary\s+Materials?|Appendix|Informed\s+Consent)\b",
]


def _trim_references(text: str) -> str:
    """Remove References/Bibliography section and everything after it."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        for pat in _END_PATTERNS:
            if re.search(pat, line.strip(), flags=re.IGNORECASE):
                return "\n".join(lines[:i]).strip()
    return text


def _strip_boilerplate_sections(text: str) -> str:
    """Remove academic boilerplate sections (acknowledgements, funding, etc.)."""
    lines = text.split("\n")
    result = []
    skipping = False
    for line in lines:
        stripped = line.strip()
        # Check if this line starts a boilerplate section
        for pat in _SKIP_SECTION_PATTERNS:
            if re.search(pat, stripped, flags=re.IGNORECASE):
                skipping = True
                break
        # A new heading that is NOT boilerplate ends the skip
        if skipping and re.match(r"^#+\s+", stripped):
            is_boilerplate = False
            for pat in _SKIP_SECTION_PATTERNS:
                if re.search(pat, stripped, flags=re.IGNORECASE):
                    is_boilerplate = True
                    break
            if not is_boilerplate:
                skipping = False
        if not skipping:
            result.append(line)
    return "\n".join(result)


def _clean_markdown(text: str) -> str:
    """Strip Docling artifacts and noisy markup from extracted markdown."""
    # Remove <!-- image --> placeholders
    text = re.sub(r'<!--\s*image\s*-->', '', text)
    # Remove standalone image links ![...](...)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    # Remove copyright / licensing boilerplate lines
    text = re.sub(
        r'^.*(?:Creative Commons|CC\s*BY|Licensee MDPI|open access article|'
        r'distributed under the terms and conditions|creativecommons\.org).*$',
        '', text, flags=re.MULTILINE | re.IGNORECASE,
    )
    # Remove author affiliation blocks (name + university/department lines)
    text = re.sub(
        r'^.*(?:Department of|Faculty of|School of|Institute of|University of|'
        r'Correspondence:|E-mail:|ORCID:).*$',
        '', text, flags=re.MULTILINE | re.IGNORECASE,
    )
    # Collapse runs of 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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

        # Clean up: strip artifacts, boilerplate, and references
        text = _clean_markdown(md_text)
        text = _strip_boilerplate_sections(text)
        text = _trim_references(text).strip()

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
