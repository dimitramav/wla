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

# ---------------------------------------------------------------------------
# Text-independence scoring (deterministic, regex-based)
# ---------------------------------------------------------------------------
# Binary metric: 1.0 if the question stands alone, 0.0 if it references the
# source material. Pattern list derived from the v1 benchmark where 92% of
# questions matched at least one of these phrases.

_TEXT_REF_PATTERN = re.compile(
    r"(?:according to|in this excerpt|based on the (?:text|passage|excerpt)"
    r"|which (?:of the following )?is NOT (?:discussed|mentioned)"
    r"|mentioned in (?:the|this)|the (?:passage|excerpt|text) (?:states|describes|discusses|suggests)"
    r"|as (?:stated|described|discussed) in"
    r"|NOT (?:a |an )?(?:factor|feature|benefit|concept|strategy) (?:discussed|mentioned)"
    r"|refer(?:s|ring) to the)",
    re.IGNORECASE,
)


def score_text_independence(raw_output: str) -> float:
    """Return 1.0 if the MCQ is text-independent, 0.0 if it references the source."""
    if not raw_output:
        return 0.0
    return 0.0 if _TEXT_REF_PATTERN.search(raw_output) else 1.0

RUBRIC_PROMPT = """You are evaluating the quality of an automatically generated multiple-choice question (MCQ) for teacher training on student mental health.

The question was generated from the source material below. A good question uses the source as factual grounding but stands alone as a professional development quiz item — it should help a teacher LEARN about student mental health, not test whether they read a specific document.

Source material (used for factual grounding):
{context}

Generated MCQ:
Stem: {stem}
Options:
{options}
Correct answer: {correct}
Explanation: {why}

Rate the MCQ on three dimensions, each from 1 (poor) to 5 (excellent):

1. stem_clarity: Is the question stem well-formed, unambiguous, and self-contained?
   5 = clear, focused, a teacher can understand exactly what is being asked without any additional context.
   3 = understandable but somewhat vague, wordy, or requires careful reading of the options to interpret.
   1 = ambiguous, fragmented, grammatically broken, or incomprehensible without additional context.

2. distractor_plausibility: Are the 3 incorrect options plausible-but-wrong — topically relevant, not trivially identifiable as wrong, and meaningfully distinct from the correct answer?
   5 = all 3 distractors represent genuine misconceptions or near-miss answers that a teacher with partial knowledge could reasonably consider.
   3 = distractors are on-topic but clearly weaker than the correct answer, or one distractor is obviously wrong.
   1 = distractors are absurd, off-topic, near-duplicates of the correct answer, or obviously nonsensical.

3. pedagogical_appropriateness: Does the question help a teacher learn or retain a meaningful concept about student mental health (risk factors, protective factors, interventions, classroom strategies)?
   5 = tests conceptual understanding, application to classroom scenarios, or meaningful relationships between concepts. A teacher who answers correctly has genuinely learned something useful.
   3 = tests a real concept but at a superficial level, or the concept has limited practical value for a teacher.
   1 = tests document-level details (e.g. "according to the passage", "which is NOT mentioned", author names, section headings, methodology), asks about trivial facts, or references the source material in the question stem.

Return strict JSON only, with no prose and no markdown fences:
{{"stem_clarity": <1-5>, "distractor_plausibility": <1-5>, "pedagogical_appropriateness": <1-5>}}
"""


def parse_mcq(parsed: dict | None) -> dict | None:
    """Normalise a parsed LLM output dict into an MCQ structure.

    Accepts the already-extracted JSON dict (produced by
    benchmarks.parsing.extract_json). Returns None if the structure is
    malformed.
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
