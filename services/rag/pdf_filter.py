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
from typing import Dict, Any, List

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


def _extract_structured(document) -> List[Dict[str, Any]]:
    """Return per-element {text, page, bbox} from a DoclingDocument.

    bbox is normalized to fractions of the page in TOPLEFT origin (l, t, r, b)
    so the frontend can draw highlight rectangles directly without a coordinate
    flip. pdf.js renders pages with y=0 at the top.
    """
    items: List[Dict[str, Any]] = []
    page_sizes: Dict[int, Any] = {}
    try:
        for page_no, page in document.pages.items():
            size = getattr(page, "size", None)
            if size is not None:
                page_sizes[page_no] = (float(size.width), float(size.height))
    except Exception:
        pass

    for text_item in getattr(document, "texts", []) or []:
        text = (getattr(text_item, "text", "") or "").strip()
        if not text:
            continue
        for prov in getattr(text_item, "prov", []) or []:
            page = getattr(prov, "page_no", None)
            bbox = getattr(prov, "bbox", None)
            if page is None or bbox is None:
                continue
            size = page_sizes.get(page)
            if not size:
                continue
            pw, ph = size
            if pw <= 0 or ph <= 0:
                continue
            l = float(bbox.l) / pw
            r = float(bbox.r) / pw
            # Docling defaults to BOTTOMLEFT origin for PDF; flip if needed.
            origin = getattr(bbox, "coord_origin", None)
            origin_name = getattr(origin, "name", str(origin or "")).upper()
            if "BOTTOM" in origin_name:
                t = 1.0 - (float(bbox.t) / ph)
                b = 1.0 - (float(bbox.b) / ph)
            else:
                t = float(bbox.t) / ph
                b = float(bbox.b) / ph
            if t > b:
                t, b = b, t
            items.append({
                "text": text,
                "page": int(page),
                "bbox": [round(l, 6), round(t, 6), round(r, 6), round(b, 6)],
            })
    return items

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
            "structured": [],
        }

    # PDF path — use Docling for ML-based extraction
    try:
        converter = _get_converter()
        result = converter.convert(str(path))
        md_text = result.document.export_to_markdown()
        structured = _extract_structured(result.document)

        # Clean up: strip artifacts, boilerplate, and references
        text = _clean_markdown(md_text)
        text = _strip_boilerplate_sections(text)
        text = _trim_references(text).strip()

        return {
            "text": text,
            "notes": "docling",
            "skipped_pages": [],
            "preview": text[:500],
            "structured": structured,
        }
    except Exception as e:
        logger.error(f"Docling failed for {path.name}: {e}")
        return {
            "text": "",
            "notes": f"docling_error: {e}",
            "skipped_pages": [],
            "preview": "",
            "structured": [],
        }
