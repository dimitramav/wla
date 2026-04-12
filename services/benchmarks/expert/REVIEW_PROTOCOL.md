# Expert Review Protocol — WLA Quiz Question Validation

## Purpose

This protocol guides expert reviewers (educational psychologists, school counselors, or teacher educators) through the systematic evaluation of AI-generated quiz questions. The questions are produced by the Watch-Listen-Act platform's RAG pipeline to train primary and secondary teachers on student mental health topics, specifically school anxiety.

Results feed directly into the thesis evaluation (Chapter 5) as evidence of content validity.

## Reviewers

- **Number of reviewers:** 2 (minimum for pairwise Cohen's Kappa)
- **Qualifications:** Domain expertise in school psychology, educational psychology, or teacher mental health training
- **Independence:** Reviewers must complete their ratings independently, without discussion

## Materials

Each reviewer receives a single `.xlsx` file containing:
1. **Instructions sheet** — embedded rating scale definitions and criteria
2. **Expert Review sheet** — 60 questions (2 sets x 3 difficulty levels x 10 per level) with locked question columns and unlocked rating columns

## Rating Criteria

### Factual Correctness (1-5)
Rate whether the question and its designated correct answer are factually accurate.

| Score | Meaning |
|-------|---------|
| 1 | Completely wrong — the correct answer is factually incorrect or the question contains false premises |
| 2 | Mostly wrong — significant factual errors that would mislead a learner |
| 3 | Partially correct — some factual issues but the core concept is sound |
| 4 | Mostly correct — minor inaccuracies that don't affect learning |
| 5 | Fully correct — factually accurate question and answer |

### Pedagogical Alignment (1-5)
Rate whether the question is appropriate and useful for training teachers on student mental health.

| Score | Meaning |
|-------|---------|
| 1 | Not at all aligned — the question has no pedagogical value for teacher training |
| 2 | Slightly aligned — tangentially related but not useful for practice |
| 3 | Moderately aligned — relevant topic but question design could be improved |
| 4 | Largely aligned — good pedagogical value with minor improvements possible |
| 5 | Completely aligned — excellent question for teacher training on this topic |

### Source Fidelity (1-5)
Rate whether the question faithfully reflects the source passage shown in the "source_snippet" column.

| Score | Meaning |
|-------|---------|
| 1 | No connection — question content has no relation to the source passage |
| 2 | Weak connection — question loosely relates to the source but makes unsupported claims |
| 3 | Partial connection — question draws from the source but adds or distorts information |
| 4 | Strong connection — question accurately reflects the source with minor extrapolation |
| 5 | Direct reflection — question is clearly and accurately derived from the source passage |

### Rationale (free text, optional)
Provide a brief explanation for any rating <= 3, or note specific issues (e.g., "correct answer should be B, not C" or "question assumes knowledge beyond beginner level").

## Procedure

1. Open the `.xlsx` file in Microsoft Excel, LibreOffice Calc, or Google Sheets
2. Read the **Instructions** sheet first
3. Switch to the **Expert Review** sheet
4. For each question row (60 total):
   a. Read the question text, options, correct answer, and source snippet
   b. Rate factual_correctness (1-5) using the dropdown
   c. Rate pedagogical_alignment (1-5) using the dropdown
   d. Rate source_fidelity (1-5) using the dropdown
   e. Optionally add rationale text, especially for any score <= 3
5. Save the file with your name appended (e.g., `expert_review_rater1.xlsx`)
6. Return the completed file to the researcher

**Estimated time:** ~1-2 minutes per question, approximately 1.5-2 hours total.

## Inter-Rater Reliability Analysis

Completed spreadsheets are analyzed using Cohen's Kappa (weighted, linear) per rating dimension:

| Kappa Range | Interpretation (Landis & Koch, 1977) |
|-------------|--------------------------------------|
| 0.81 - 1.00 | Almost perfect agreement |
| 0.61 - 0.80 | Substantial agreement |
| 0.41 - 0.60 | Moderate agreement |
| 0.21 - 0.40 | Fair agreement |
| 0.00 - 0.20 | Slight agreement |
| < 0.00 | Poor (less than chance) |

Linear weights are used because the Likert scale is ordinal — a disagreement of 1 vs 5 is more severe than 4 vs 5.

Raw agreement percentage is also reported alongside Kappa to account for the Kappa paradox (high agreement with skewed distributions can yield deceptively low Kappa values).

## Thesis Integration

- **Chapter:** 5 — Evaluation
- **Section:** Expert Validation of Question Quality
- **Reports:** Per-dimension Kappa scores, raw agreement percentages, interpretation
- **Discussion points:** Agreement patterns across difficulty levels, common failure modes identified by experts, implications for RAG pipeline quality

## References

- McHugh, M. L. (2012). Interrater reliability: the kappa statistic. *Biochemia Medica*, 22(3), 276-282.
- Hallgren, K. A. (2012). Computing inter-rater reliability for observational data: An overview and tutorial. *Tutorials in Quantitative Methods for Psychology*, 8(1), 23-34.
- Gwet, K. L. (2014). *Handbook of inter-rater reliability: The definitive guide to measuring the extent of agreement among raters* (4th ed.). Advanced Analytics, LLC.
