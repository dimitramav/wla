import os, json, time, hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load once at import; adjust path if your notebooks live elsewhere
load_dotenv(Path("../.env"))

CONTENT_DIR   = Path(os.getenv("RAG_CONTENT_DIR", "../content"))
CHROMA_DIR    = Path(os.getenv("RAG_CHROMA_DIR", "rag/chroma"))
DOCSETS_META  = Path(os.getenv("RAG_DOCSETS_META", "rag/docsets.json"))
EMB_MODEL_ID  = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")

CHROMA_DIR.mkdir(parents=True, exist_ok=True)
DOCSETS_META.parent.mkdir(parents=True, exist_ok=True)
if not DOCSETS_META.exists():
    DOCSETS_META.write_text("{}", encoding="utf-8")

@dataclass
class FileSig:
    name: str
    size: int
    mtime: float

def read_docsets_meta() -> Dict[str, Any]:
    try:
        return json.loads(DOCSETS_META.read_text(encoding="utf-8"))
    except Exception:
        return {}

def write_docsets_meta(data: Dict[str, Any]) -> None:
    DOCSETS_META.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_topic_dir(topic: str) -> Path:
    return (CONTENT_DIR / topic).resolve()

def collect_documents(topic: str) -> List[Path]:
    root = get_topic_dir(topic)
    if not root.exists():
        return []
    exts = ("*.pdf", "*.md", "*.txt")
    files = []
    for ext in exts:
        for p in root.rglob(ext):
            if p.is_file() and "pdfs_original" not in p.parts:
                files.append(p)
    return sorted(files, key=lambda p: p.name)

def file_signature(p: Path) -> FileSig:
    st = p.stat()
    return FileSig(name=str(p.name), size=st.st_size, mtime=st.st_mtime)

def compute_docset_hash(files: List[Path]) -> str:
    sigs = [file_signature(p) for p in files]
    sigs_sorted = sorted([asdict(s) for s in sigs], key=lambda d: (d["name"], d["size"], d["mtime"]))
    blob = json.dumps(sigs_sorted, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
