"""Parity test: plan_only must return the same targeted_keywords as generate_qg for
the same (topic, docset_hash, keywords, weak_keywords, mix, seed, weak_focus_ratio).
This is the non-negotiable D-16 check that the LLM-free shortcut matches the live scheduler.

Prerequisites:
- Ollama must be running on localhost:11434 with gemma2:9b-instruct-q4_0 available
  (generate_qg calls the LLM; plan_only does not).
- FastAPI is NOT required: ingest_topic reads/writes Chroma directly on disk.
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rag.qg import generate_qg, plan_only
from rag.ingest import ingest_topic

TOPIC = "school_anxiety"
KEYWORDS = [
    "common signs and symptoms",
    "peer aggression",
    "social evaluation fears",
    "somatic complaints",
    "attendance tracking",
]
WEAK = ["peer aggression", "somatic complaints"]
MIX = {"mcq": 3, "yesno": 2}
SEED = "parity-seed-1"
RATIO = 0.65


@pytest.fixture(scope="module")
def docset_hash():
    res = ingest_topic(TOPIC, force=False)
    return res.get("docset_hash", "")


def test_plan_only_parity_with_generate_qg(docset_hash):
    assert docset_hash, "Ingestion did not return a docset_hash"

    live = generate_qg(
        topic=TOPIC,
        docset_hash=docset_hash,
        mix=MIX,
        seed=SEED,
        keywords=KEYWORDS,
        weak_keywords=WEAK,
        weak_focus_ratio=RATIO,
        retrieval_type="dense",
    )
    live_targets = [q["keywords"][0] if q["keywords"] else None for q in live["questions"]]

    sim = plan_only(
        topic=TOPIC,
        docset_hash=docset_hash,
        mix=MIX,
        keywords=KEYWORDS,
        weak_keywords=WEAK,
        weak_focus_ratio=RATIO,
        retrieval_type="dense",
    )
    sim_targets = sim["targeted_keywords"]

    assert len(live_targets) == len(sim_targets), (
        f"Length mismatch: live={len(live_targets)} sim={len(sim_targets)}"
    )
    assert live_targets == sim_targets, (
        f"Targeting drift — live={live_targets} sim={sim_targets}"
    )
    assert sim["weak_slot_n"] == int(sum(MIX.values()) * RATIO)
