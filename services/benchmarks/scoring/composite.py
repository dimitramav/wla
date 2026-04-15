"""
Composite score for the LLM benchmark (v3 formula).

v3: 0.30 faithfulness + 0.25 context_relevancy + 0.20 mcq_quality
    + 0.15 text_independence + 0.10 format_compliance

v2 (superseded — see LLM_BENCHMARK_METHODOLOGY.md §6):
    0.4*faithfulness + 0.3*context_relevancy + 0.2*mcq_quality + 0.1*format_compliance
    Missing text_independence caused v2 to penalise standalone questions
    because RAGAS faithfulness rewards surface overlap with source chunks.

v1 (superseded — see LLM_BENCHMARK_REPORT.md Findings 4 and 5):
    0.4*faithfulness + 0.4*context_relevancy + 0.1*answer_relevancy + 0.1*format_compliance

text_independence (binary 0/1, regex-scored) captures whether the question
stands alone without referencing source material — the primary quality
dimension that the prompt revision targeted. faithfulness reduced from 0.40
to 0.30 because its 0–1 range double-counts text-dependence (text-referencing
questions are trivially faithful).
"""


def composite_score(faithfulness, context_relevancy, mcq_quality,
                    text_independence, format_compliance):
    vals = [faithfulness, context_relevancy, mcq_quality,
            text_independence, format_compliance]
    if any(v is None for v in vals):
        return None
    return round(
        (faithfulness * 0.30)
        + (context_relevancy * 0.25)
        + (mcq_quality * 0.20)
        + (text_independence * 0.15)
        + (format_compliance * 0.10),
        4,
    )
