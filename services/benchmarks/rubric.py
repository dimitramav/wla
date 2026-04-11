"""
Shared MCQ-quality rubric scoring for the LLM benchmark.

Adds a task-specific MCQ quality signal that replaces RAGAS answer_relevancy
in the composite score. See LLM_BENCHMARK_REPORT.md Finding 5 for the
investigation that motivated the swap; Finding 4 documents why
answer_relevancy was a weak discriminator on MCQ generation.

The judge (Gemini 2.5 Flash Lite) rates each generated MCQ on three
dimensions 1-5:
  - stem_clarity
  - distractor_plausibility
  - pedagogical_appropriateness

mcq_quality = mean(three dimensions) / 5   (normalised to 0..1)

Rubric adapted from the Med-PaLM clinical QA protocol (Singhal et al., 2023)
and targets the MCQ-specific quality dimensions identified by Kurdi et al.
(2020) in their systematic review of automatic question generation for
educational purposes.
"""

import json
import re
import time

RUBRIC_PROMPT = """You are evaluating the quality of an automatically generated multiple-choice question (MCQ) for teacher training on student mental health.

Source context (the excerpt the question was generated from):
{context}

Generated MCQ:
Stem: {stem}
Options:
{options}
Correct answer: {correct}
Explanation: {why}

Rate the MCQ on three dimensions, each from 1 (poor) to 5 (excellent):

1. stem_clarity: Is the question stem well-formed, unambiguous, and self-contained?
   5 = clear, focused, a reader can understand exactly what is being asked.
   1 = ambiguous, fragmented, grammatically broken, or requires reading the options to understand.

2. distractor_plausibility: Are the 3 incorrect options plausible-but-wrong - topically relevant, not trivially identifiable as wrong, and meaningfully distinct from the correct answer?
   5 = all 3 distractors are genuine competitors that a learner could reasonably consider.
   1 = distractors are absurd, off-topic, near-duplicates of the correct answer, or obviously nonsensical.

3. pedagogical_appropriateness: Does the question probe meaningful understanding of the context rather than superficial recall of a specific phrase?
   5 = tests conceptual understanding or application.
   1 = trivial fact lookup, tests phrasing rather than content, or is off-topic relative to the excerpt.

Return strict JSON only, with no prose and no markdown fences:
{{"stem_clarity": <1-5>, "distractor_plausibility": <1-5>, "pedagogical_appropriateness": <1-5>}}
"""


def parse_mcq(parsed: dict | None) -> dict | None:
    """Normalise a parsed LLM output dict into an MCQ structure.

    Accepts the already-extracted JSON dict (produced by
    llm_benchmark.extract_json). Returns None if the structure is malformed.
    """
    if not isinstance(parsed, dict):
        return None
    stem = str(parsed.get("text") or "").strip()
    options = parsed.get("options") or []
    correct = str(parsed.get("correct") or "").strip().upper()
    why = str(parsed.get("why") or "").strip()
    if not stem or not isinstance(options, list) or len(options) != 4:
        return None
    if correct not in ("A", "B", "C", "D"):
        return None
    return {
        "stem": stem,
        "options": [str(o) for o in options],
        "correct": correct,
        "why": why,
    }


def _format_prompt(mcq: dict, context: list[str]) -> str:
    options_text = "\n".join(f"  {opt}" for opt in mcq["options"])
    context_text = "\n\n".join(context) if context else "(no context)"
    return RUBRIC_PROMPT.format(
        context=context_text,
        stem=mcq["stem"],
        options=options_text,
        correct=mcq["correct"],
        why=mcq["why"],
    )


def score_mcq(llm, mcq: dict, context: list[str]) -> dict | None:
    """Call the judge LLM with the rubric prompt and parse the JSON response.

    `llm` must be a langchain chat model with an .invoke(prompt) method
    (e.g. ChatGoogleGenerativeAI). Not a RAGAS wrapper.

    Returns a dict with stem_clarity, distractor_plausibility,
    pedagogical_appropriateness (each 1-5 int) and mcq_quality (0-1 float),
    or None on failure.
    """
    prompt = _format_prompt(mcq, context)

    for attempt in range(1, 4):
        try:
            resp = llm.invoke(prompt)
            text = resp.content if hasattr(resp, "content") else str(resp)
            match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
            if not match:
                return None
            obj = json.loads(match.group(0))
            scores = {
                "stem_clarity": int(obj["stem_clarity"]),
                "distractor_plausibility": int(obj["distractor_plausibility"]),
                "pedagogical_appropriateness": int(obj["pedagogical_appropriateness"]),
            }
            for v in scores.values():
                if not 1 <= v <= 5:
                    return None
            scores["mcq_quality"] = round(
                (scores["stem_clarity"]
                 + scores["distractor_plausibility"]
                 + scores["pedagogical_appropriateness"]) / 3 / 5,
                4,
            )
            return scores
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < 3:
                time.sleep(30 * attempt)
                continue
            if attempt == 3:
                return None
            time.sleep(2)
    return None


def composite_score(faithfulness, context_relevancy, mcq_quality, format_compliance):
    """Weighted composite v2: 0.4 faith + 0.3 ctx + 0.2 mcq_quality + 0.1 fmt.

    Replaces the v1 formula that used answer_relevancy at 0.1 and
    context_relevancy at 0.4 (see LLM_BENCHMARK_REPORT.md Finding 5).
    """
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
