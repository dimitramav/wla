"""
Composite score for the LLM benchmark (v2 formula).

v2: 0.4 faithfulness + 0.3 context_relevancy + 0.2 mcq_quality + 0.1 format_compliance

v1 (superseded — see LLM_BENCHMARK_REPORT.md Findings 4 and 5):
    0.4*faithfulness + 0.4*context_relevancy + 0.1*answer_relevancy + 0.1*format_compliance

answer_relevancy was a weak discriminator on MCQ-generation (Finding 4);
replaced by the task-specific rubric-based mcq_quality signal (Finding 5).
context_relevancy dropped from 0.4 to 0.3 to give the rubric 0.2;
faithfulness kept at 0.4 as the safety-critical anchor.
"""


def composite_score(faithfulness, context_relevancy, mcq_quality, format_compliance):
    vals = [faithfulness, context_relevancy, mcq_quality, format_compliance]
    if any(v is None for v in vals):
        return None
    return round(
        (faithfulness * 0.4)
        + (context_relevancy * 0.3)
        + (mcq_quality * 0.2)
        + (format_compliance * 0.1),
        4,
    )
