"""Proves plan_only does not invoke the LLM and does not write retrieval_logs.jsonl.
If either leak regresses, the Phase 9 simulation budget and observability assumptions break."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rag.qg import plan_only, RETRIEVAL_LOG
from rag.ingest import ingest_topic

TOPIC = "school_anxiety"
KEYWORDS = [
    "common signs and symptoms",
    "peer aggression",
    "social evaluation fears",
    "somatic complaints",
    "attendance tracking",
]


def _sentinel(*args, **kwargs):
    raise RuntimeError("plan_only must not call llm.client.generate_json")


def test_plan_only_does_not_call_llm():
    docset_hash = ingest_topic(TOPIC, force=False).get("docset_hash", "")
    with patch("llm.client.generate_json", side_effect=_sentinel):
        result = plan_only(
            topic=TOPIC,
            docset_hash=docset_hash,
            mix={"mcq": 3, "yesno": 2},
            keywords=KEYWORDS,
            weak_keywords=["peer aggression"],
            weak_focus_ratio=0.6,
        )
    assert "targeted_keywords" in result
    assert len(result["targeted_keywords"]) == 5


def test_plan_only_does_not_write_retrieval_log():
    docset_hash = ingest_topic(TOPIC, force=False).get("docset_hash", "")
    before = RETRIEVAL_LOG.stat().st_size if RETRIEVAL_LOG.exists() else 0
    for _ in range(5):
        plan_only(
            topic=TOPIC,
            docset_hash=docset_hash,
            mix={"mcq": 2, "yesno": 1},
            keywords=KEYWORDS,
            weak_keywords=["peer aggression"],
            weak_focus_ratio=0.65,
        )
    after = RETRIEVAL_LOG.stat().st_size if RETRIEVAL_LOG.exists() else 0
    assert after == before, (
        f"plan_only wrote to retrieval_logs.jsonl (before={before} after={after})"
    )
