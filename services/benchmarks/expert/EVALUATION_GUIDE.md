# Post-Review Evaluation Guide

## What you need

- Two completed `.xlsx` files (one from each expert reviewer)
- Python environment with project dependencies installed

## Step-by-step

### 1. Collect the completed spreadsheets

Each reviewer should return their file with ratings filled in (columns: factual_correctness, pedagogical_alignment, source_fidelity, and optionally rationale).

Rename them clearly:

```
expert_review_rater1.xlsx
expert_review_rater2.xlsx
```

Place both files in `services/benchmarks/results/`.

### 2. Quick visual inspection

Before running the analysis, open each file and check:

- All 60 rows have ratings (no blank Likert cells)
- Ratings are integers 1-5 (the dropdown should enforce this, but verify)
- If any rows are blank, the script will skip them — but more than a few missing rows weakens the analysis

### 3. Run the Kappa analysis

```bash
cd services
python -m benchmarks.expert.kappa \
  --rater-a benchmarks/results/expert_review_rater1.xlsx \
  --rater-b benchmarks/results/expert_review_rater2.xlsx
```

This produces a Markdown report in `benchmarks/results/expert_kappa_<timestamp>.md`.

**Note:** The script reads from the "Expert Review" sheet. If your XLSX has tabs named "Set 1" / "Set 2" instead, you will need to either:
- Rename the tab to "Expert Review" before running, or
- Run the script once per tab (rename each tab to "Expert Review", save, run)

### 4. Interpret the results

The report contains a table like:

| Dimension | Kappa | Raw Agreement | Interpretation |
|-----------|-------|---------------|----------------|
| factual_correctness | 0.750 | 80.0% | Substantial |
| pedagogical_alignment | 0.600 | 70.0% | Moderate |
| source_fidelity | 0.820 | 85.0% | Almost Perfect |

**Kappa interpretation (Landis & Koch, 1977):**

| Kappa | Meaning | What it means for your thesis |
|-------|---------|-------------------------------|
| 0.81-1.00 | Almost Perfect | Strong evidence of content validity |
| 0.61-0.80 | Substantial | Good evidence — minor disagreements are normal |
| 0.41-0.60 | Moderate | Acceptable but worth discussing in limitations |
| 0.21-0.40 | Fair | Weak — investigate which questions caused disagreement |
| < 0.20 | Slight/Poor | Problematic — consider revising questions or criteria |

**Raw agreement** is reported alongside Kappa because of the Kappa paradox: when most ratings cluster around one value (e.g., both reviewers give 4 or 5 to almost everything), Kappa can be misleadingly low despite high actual agreement. If raw agreement is high but Kappa is low, mention this in your thesis discussion.

### 5. What to look for

**Good outcome (Kappa >= 0.61 on all dimensions):**
- Report the numbers in Chapter 5
- Conclude that the RAG pipeline produces questions with validated content quality

**Mixed outcome (some dimensions below 0.61):**
- Check the rationale column for low-scoring questions — reviewers may explain what went wrong
- Look for patterns: are disagreements concentrated in a specific difficulty level or keyword?
- Discuss in limitations: which dimension was weaker and why

**Poor outcome (Kappa < 0.41 on any dimension):**
- Identify the specific questions where reviewers diverged (compare ratings row by row)
- Consider whether the rating criteria were ambiguous
- Report honestly — low agreement is still a valid finding that informs future work

### 6. Deeper analysis (optional)

To break down agreement by difficulty level, filter the rows in Excel before running the analysis:

1. Copy the XLSX
2. Delete rows that are not the target level (e.g., keep only "beginner")
3. Run kappa.py on the filtered file
4. Repeat for "intermediate" and "advanced"

This tells you if question quality varies by difficulty — useful for the thesis discussion.

### 7. Writing it up (Chapter 5)

Structure for the Expert Validation section:

1. **Method** — 2 reviewers, 60 questions, 3 Likert dimensions, Cohen's Kappa with linear weights
2. **Results** — table of Kappa + raw agreement per dimension
3. **Discussion** — interpretation, patterns across difficulty levels, any problematic questions identified by reviewers
4. **Limitations** — sample size (60 questions, 2 raters), Kappa paradox if applicable

Key references to cite:
- McHugh, M. L. (2012). Interrater reliability: the kappa statistic. *Biochemia Medica*, 22(3), 276-282.
- Hallgren, K. A. (2012). Computing inter-rater reliability for observational data. *Tutorials in Quantitative Methods for Psychology*, 8(1), 23-34.
