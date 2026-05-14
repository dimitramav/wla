"""
Column definitions, validation rules, and constants for the expert review spreadsheet.
"""

QUESTION_COLS = [
    "question_text",
    "correct_answer",
    "options",
    "explanation",
    "source_document",
    "keyword",
    "difficulty_level",
]

RATING_COLS = [
    "factual_correctness",      # Likert 1-5
    "pedagogical_alignment",    # Likert 1-5
    "source_fidelity",          # Likert 1-5
    "rationale",                # free text
]

LIKERT_COLS = ["factual_correctness", "pedagogical_alignment", "source_fidelity"]

ALL_COLS = QUESTION_COLS + RATING_COLS

LIKERT_LABELS = {
    1: "Completely wrong / Not at all",
    2: "Mostly wrong / Slightly",
    3: "Partially correct / Moderately",
    4: "Mostly correct / Largely",
    5: "Fully correct / Completely",
}

LEVELS = ["beginner", "intermediate", "advanced"]
N_PER_LEVEL = 10
N_SETS = 2
