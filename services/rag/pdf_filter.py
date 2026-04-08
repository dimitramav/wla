# This file provides utilities for filtering and extracting relevant sections from research PDFs.
#
# Key Features:
# - Identifies and trims front matter and tail sections of research papers.
# - Uses heuristics to detect introduction and reference sections.
# - Extracts and processes text from PDF files.
#
# Dependencies:
# - PyPDF for reading and extracting text from PDFs.
# - Regular expressions for pattern matching.

# Simple research-article filter: trims front matter and tail sections.
# Works for most papers; later upgrade to GROBID/Docling for robust sectionization.
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from pypdf import PdfReader

START_HEADERS = [
    r"^\s*(\d+(\.\d+)*)?\s*Introduction\b",
    r"^\s*[IVX]+\.\s*Introduction\b",
    r"^\s*Background\b",
    r"^\s*(Materials\s+and\s+)?Methods\b",
    r"^\s*Materials\s+and\s+Methods\b",
    r"^\s*Methodology\b",
]
END_HEADERS = [
    r"^\s*References\b",
    r"^\s*Bibliography\b",
    r"^\s*Acknowledge?ments?\b",
    r"^\s*Appendix\b",
    r"^\s*Supplementary\b",
]
FRONT_TOKENS = [
    "doi:", "arxiv", "affiliations", "corresponding author", "@",
    "creativecommons", "received", "accepted", "published", "rights reserved"
]

# Read all pages from a PDF file

def _read_pdf_pages(path: Path) -> List[str]:
    reader = PdfReader(str(path))
    out = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        out.append(txt.strip())
    return out

# Check if text resembles front matter based on heuristics
def _looks_like_front_matter(text: str) -> bool:
    low = text.lower()
    hits = sum(tok in low for tok in FRONT_TOKENS)
    return hits >= 2 or len(text.split()) < 150

# Find the index of a line matching any pattern
def _find_index(lines: List[str], patterns: List[str]) -> Optional[int]:
    for i, ln in enumerate(lines):
        for pat in patterns:
            if re.search(pat, ln, flags=re.IGNORECASE):
                return i
    return None

# Filter and extract relevant sections from a document (PDF, MD, or TXT)
def filter_document(path: Path) -> Dict[str, Any]:
    # For plain text and markdown files, read directly — no PyPDF needed
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

    # PDF path — use existing heuristic filtering
    pages = _read_pdf_pages(path)
    if not pages:
        return {"text": "", "notes": "no_pages", "skipped_pages": [], "preview": ""}

    lines, line_page_idx = [], []
    for pi, pg in enumerate(pages):
        for ln in (pg.splitlines() or [""]):
            lines.append(ln.strip())
            line_page_idx.append(pi)

    start_idx = _find_index(lines, START_HEADERS)
    skipped_pages = []
    if start_idx is None:
        for i in range(min(3, len(pages))):
            if _looks_like_front_matter(pages[i]):
                skipped_pages.append(i)
        if skipped_pages:
            first_keep_page = max(skipped_pages) + 1
            for i, pg in enumerate(line_page_idx):
                if pg >= first_keep_page and lines[i]:
                    start_idx = i
                    break

    end_idx = _find_index(lines, END_HEADERS)

    if start_idx is None:
        body = lines
        note = "start=not_found"
    else:
        if end_idx is not None and end_idx > start_idx:
            body = lines[start_idx:end_idx]
            note = "start=ok;end=ok"
        else:
            body = lines[start_idx:]
            note = "start=ok;end=not_found"

    text = "\n".join(body).strip()
    return {
        "text": text,
        "notes": note,
        "skipped_pages": skipped_pages,
        "preview": "\n".join(body[:10])
    }

# Backward-compatible alias
filter_research_pdf = filter_document
