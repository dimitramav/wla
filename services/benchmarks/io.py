"""
CSV and context-lookup helpers shared across the benchmark pipelines.
"""

import csv
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


def find_latest_csv(prefix: str, explicit: str | None = None, results_dir: Path = RESULTS_DIR) -> Path:
    """Find the most recent benchmark CSV for a given prefix (rag / llm)."""
    if explicit:
        p = results_dir / explicit if not Path(explicit).is_absolute() else Path(explicit)
        if p.exists():
            return p
        raise FileNotFoundError(f"CSV not found: {p}")
    csvs = sorted(results_dir.glob(f"{prefix}_*.csv"), reverse=True)
    if not csvs:
        raise FileNotFoundError(f"No {prefix}_*.csv found in {results_dir}")
    return csvs[0]


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})


def build_context_lookup(rag_rows: list[dict]) -> dict:
    """Build a lookup: (emb_model, chunk_size, chunk_overlap, retrieval_type, question) -> contexts list."""
    lookup = {}
    for r in rag_rows:
        key = (
            r["emb_model"],
            r["chunk_size"],
            r["chunk_overlap"],
            r["retrieval_type"],
            r["question"],
        )
        contexts_raw = r.get("contexts_text", "")
        lookup[key] = contexts_raw.split("|||") if contexts_raw else []
    return lookup
