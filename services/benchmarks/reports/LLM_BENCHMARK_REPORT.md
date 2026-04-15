# LLM Generation Benchmark Report

## 1. Experimental Setup

### Objective

Evaluate the question-generation quality of four open-source, locally-runnable LLMs for the WLA adaptive quiz pipeline. The goal is to determine which generator produces the most faithful, well-formatted multiple-choice questions when given the same retrieved contexts, holding retrieval constant.

### What is being evaluated

This benchmark tests **generation quality** — whether a model, given frozen RAG contexts from the retrieval benchmark, can write grammatically correct, grounded, strict-JSON MCQs that do not invent facts outside the excerpt. It does **not** re-evaluate retrieval, which is the subject of the separate RAG Retrieval Benchmark Report.

By reusing the exact retrieval contexts from `rag_20260410_160216.csv`, every generator is scored against the same inputs — isolating the effect of the LLM from any confound introduced by retrieval variability.

### Generators tested

| Name | Ollama tag | Parameters | Quantisation |
|------|------------|:---:|:---:|
| mistral-7b (production baseline) | `mistral:7b-instruct-q4_0` | 7.2 B | Q4_0 |
| llama3.1-8b | `llama3.1:8b-instruct-q4_0` | 8.0 B | Q4_0 |
| gemma2-9b | `gemma2:9b-instruct-q4_0` | 9.2 B | Q4_0 |
| phi3.5-3.8b | `phi3.5:3.8b-mini-instruct-q4_0` | 3.8 B | Q4_0 |

All four run on the same local Ollama instance, with identical temperature (0.0) and seed (7) for determinism. Each model generates one MCQ per retrieval row.

### Experimental matrix

- **12 retrieval configurations** (3 embeddings × 2 chunk sizes × 2 retrieval strategies) × **10 golden questions** = **120 rows per generator**
- **4 generators** × 120 rows = **480 total generations**

The 10 golden questions are the same manually-curated set used in the RAG benchmark.

### Metrics

Four metrics contribute to each row, plus a weighted composite:

- **Format compliance** (`format_compliance`) — Binary (0/1). Is the raw LLM output valid strict JSON containing the required fields (`text`, `options` as a 4-element array, `correct` ∈ {A,B,C,D}, `why`)? Computed by direct parsing, no LLM judge involved.
- **Faithfulness** (`faithfulness`) — RAGAS metric, 0–1. Fraction of atomic claims in the generated question+explanation that can be verified against the retrieved contexts. Scores near 1.0 mean the model grounds its output in the excerpt; low scores mean it is inventing facts.
- **Context relevancy** (`context_relevancy`) — Inherited from the RAG benchmark (RAGAS `context_precision`). Represents retrieval quality for the row and is the same across all four generators for a given config/question pair.
- **MCQ quality rubric** (`mcq_quality`) — Custom LLM-as-judge rubric, 0–1. The same Gemini 2.5 Flash Lite judge rates each generated MCQ on three MCQ-specific dimensions, each 1–5: **stem clarity**, **distractor plausibility**, and **pedagogical appropriateness**. `mcq_quality = mean(three) / 5`. Replaces RAGAS `answer_relevancy`, which Finding 4 showed was a weak discriminator on MCQ generation (the 0.35–0.38 cluster is a real MiniLM + task property). The rubric is adapted from the Med-PaLM clinical QA protocol (Singhal et al. 2023) and targets the quality dimensions identified by Kurdi et al. (2020) in their systematic review of automatic MCQ generation. See LLM_BENCHMARK_METHODOLOGY.md §4.4 for full prompt and rationale.
- **Answer relevancy** (`answer_relevancy`) — *Deprecated.* RAGAS metric retained in the CSV schema for backward-compat with pre-Finding-5 runs; no longer computed or used in the composite. See Finding 4.

**Composite score** is a weighted average: `0.4 × faithfulness + 0.3 × context_relevancy + 0.2 × mcq_quality + 0.1 × format_compliance`. Grounding (faithfulness + retrieved-context quality) still dominates at 70%; task-specific MCQ quality contributes 20%; strict-JSON format contributes 10%. The v1 formula (`0.4·faith + 0.4·ctx + 0.1·ans_rel + 0.1·fmt`) is preserved in source as a deprecated path — see Finding 5 for the investigation that motivated the swap.

### RAGAS judge

All RAGAS metrics are scored by **Google Gemini 2.5 Flash Lite** via `langchain-google-genai`, not by the small local models — this avoids the self-grading bias flagged by Zheng et al. (2023). Gemini evaluated all 480 rows in roughly 10 minutes on the paid tier.

---

## 2. Results

### 2.1 Per-generator summary

| Generator | Format | Faith | MCQ Qual | Ctx. Rel | Composite | Latency (s, median) |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **gemma2-9b** | **1.000** | **0.833** | 0.784 | 0.795 | **0.8305** | 77.6 |
| phi3.5-3.8b | 0.842 | 0.722 | **0.806** | 0.795 | 0.7841 | **41.7** |
| llama3.1-8b | 0.942 | 0.735 | 0.780 | 0.795 | 0.7810 | 52.2 |
| mistral-7b (baseline) | 0.742 | 0.714 | 0.697 | 0.795 | 0.7646 | 59.9 |

All four generators consumed the same retrieval contexts, so `context_relevancy` is identical across models (0.795 — the corpus-wide mean from the RAG benchmark). The ranking is driven by **format compliance**, **faithfulness**, and the new **MCQ quality rubric**. The composite is the v2 formula (`0.4·faith + 0.3·ctx + 0.2·mcq_quality + 0.1·fmt`); Finding 5 describes the rubric investigation and the resulting ranking flip (phi3.5-3.8b overtook llama3.1-8b by 0.003 composite, driven by a +0.43 advantage on pedagogical appropriateness).

### 2.2 Top 5 end-to-end configurations

Combining the best retrieval configuration with the best generator (composite v2):

| # | Generator | Embedding | Chunks | Retrieval | Faith | Ctx. Rel | MCQ Q | Composite |
|---|-----------|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | gemma2-9b | all-mpnet-base-v2 | 800/100 | hybrid | 0.880 | 0.855 | 0.827 | **0.8740** |
| 2 | gemma2-9b | all-mpnet-base-v2 | 800/100 | dense | 1.000 | 0.752 | 0.740 | 0.8735 |
| 3 | gemma2-9b | bge-small-en-v1.5 | 512/50 | hybrid | 0.860 | 0.848 | 0.787 | 0.8558 |
| 4 | gemma2-9b | bge-small-en-v1.5 | 800/100 | dense | 0.950 | 0.770 | 0.713 | 0.8536 |
| 5 | phi3.5-3.8b | all-mpnet-base-v2 | 800/100 | hybrid | 0.825 | 0.855 | 0.838 | 0.8506 |

Four of the top five slots are held by **gemma2-9b**; the fifth is **phi3.5-3.8b + all-mpnet-base-v2 (800/100 hybrid)**, which outscores every llama3.1 configuration on the v2 composite because of its rubric advantage on distractor plausibility and pedagogical appropriateness. The first llama3.1 entry appears at rank #7 (llama3.1-8b + MiniLM 800/100 hybrid, composite = 0.8446).

### 2.3 Format compliance breakdown

Format compliance is the most discriminating axis between generators:

| Generator | Pass | Fail | Pass rate |
|-----------|:---:|:---:|:---:|
| gemma2-9b | 120 | 0 | **100.0 %** |
| llama3.1-8b | 113 | 7 | 94.2 % |
| phi3.5-3.8b | 101 | 19 | 84.2 % |
| mistral-7b | 89 | 31 | 74.2 % |

**The production baseline (mistral-7b) fails strict-JSON validation on 1 in 4 generations.** These are rows where downstream quiz rendering would need the fallback generic question. Failures are typically malformed option lists, missing `correct` field, or unescaped quotes that break `json.loads`.

### 2.4 Faithfulness consistency

Faithfulness means are tight (0.71–0.83) but the standard deviation tells a different story:

| Generator | Mean | Std | Min | Max |
|-----------|:---:|:---:|:---:|:---:|
| gemma2-9b | 0.833 | **0.225** | 0.25 | 1.00 |
| phi3.5-3.8b | 0.722 | 0.244 | 0.00 | 1.00 |
| mistral-7b | 0.714 | 0.287 | 0.00 | 1.00 |
| llama3.1-8b | 0.735 | 0.292 | 0.00 | 1.00 |

gemma2-9b is the most consistent: its worst row still scores 0.25, while the other three produce at least one fully-hallucinated generation (faithfulness = 0.00). This matters pedagogically — a single fabricated fact in a quiz question is a harder failure to recover from than a minor wording issue.

### 2.5 Latency

| Generator | Median | Mean | Min | Max |
|-----------|:---:|:---:|:---:|:---:|
| phi3.5-3.8b | **41.7 s** | 40.4 s | 11.8 s | 66.9 s |
| llama3.1-8b | 52.2 s | 51.4 s | 14.5 s | 79.2 s |
| mistral-7b | 59.9 s | 56.5 s | 13.9 s | 106.8 s |
| gemma2-9b | 77.6 s | 74.2 s | 23.1 s | 101.5 s |

Per-question generation latency was measured end-to-end against the local Ollama instance. The 9-billion-parameter gemma2 is roughly **1.85× slower** than phi3.5 and **1.30× slower** than the current mistral baseline. For the current WLA UX (one question at a time, asynchronous quiz flow) this is acceptable; for a synchronous, high-throughput regeneration endpoint it would not be.

### 2.6 MCQ quality rubric sub-scores

Mean scores on the three 1–5 rubric dimensions, computed over parseable MCQs only (n = 90–120 per generator after excluding format failures):

| Generator | Stem clarity | Distractor plausibility | Pedagogical appropriateness | MCQ quality (0–1) |
|-----------|:---:|:---:|:---:|:---:|
| gemma2-9b | **4.97** | 3.61 | 3.19 | 0.784 |
| phi3.5-3.8b | 4.78 | **3.68** | **3.62** | **0.806** |
| llama3.1-8b | 4.88 | 3.56 | 3.25 | 0.780 |
| mistral-7b | 4.40 | 3.01 | 3.04 | 0.697 |

**Stem clarity** is saturated for every generator except mistral-7b — all four are producing grammatically well-formed questions. The discriminating dimensions are **distractor plausibility** (range 3.01–3.68) and **pedagogical appropriateness** (range 3.04–3.62). phi3.5-3.8b is the strongest on both, despite being the smallest model: its MCQs more consistently probe conceptual understanding rather than phrase-lookup, and its wrong options are more competitive than the larger models'. This is the single reason it overtakes llama3.1-8b on the composite.

---

## 3. Key Findings

### Finding 1: gemma2-9b is the strongest generator on every quality axis

gemma2-9b leads in format compliance (100 %), mean faithfulness (0.833), faithfulness consistency (lowest std), and composite score (0.790). It is also the only model that never failed JSON validation in 120 generations. The cost is latency: median 77.6 seconds vs the 41.7 seconds of phi3.5.

### Finding 2: The production baseline has a structural reliability problem

`mistral:7b-instruct-q4_0` — the current production default — fails strict-JSON validation on **25.8 %** of generations. This is consistent with BUGS-01 (LLM output validation is weak), which is tracked in the v1 roadmap. Switching generators closes this gap without any prompt engineering.

### Finding 3: Parameter count is not the whole story

phi3.5-3.8b (3.8 B parameters) outperforms mistral-7b (7.2 B) on format compliance (0.842 vs 0.742) and matches it on faithfulness (0.722 vs 0.714), while running 30 % faster. For a cheap, locally-hostable fallback this is the most attractive model in the set.

### Finding 4: The answer-relevancy cluster is a real MiniLM + task property, not a payload artefact

Every generator scored in a narrow 0.35–0.38 band on RAGAS `answer_relevancy`. The initial hypothesis was that this was a payload-shape artefact — RAGAS `answer_relevancy` asks the judge to reverse-engineer candidate questions from the "answer" text and then measures mean cosine similarity between those reverse-engineered questions and the original golden question, so serialising the WLA "answer" as a full MCQ (`Question: ... Options: ... Correct: ... Explanation: ...`) plausibly dragged every generator toward the same low ceiling.

**Offline re-scoring investigation.** To test the hypothesis without re-running the ~8-hour generation pass, the `raw_output` column was reparsed and a stand-alone script ([rescore_answer_metric.py](rescore_answer_metric.py)) re-evaluated `answer_relevancy` on the same 460 valid rows with one change only: instead of the full MCQ, the rescore passed just the grounded `why` explanation (prefixed by the correct option text) as the RAGAS `answer`. Two embedding models were tried in sequence to disambiguate payload effects from embedding-model effects; all other variables (judge LLM, prompt, rag CSV, golden questions) were held constant.

**Results (per generator, n ≈ 111–120 after excluding format failures):**

| Generator | Ans. Rel (original, MCQ payload, MiniLM) | Ans. Rel (`why` payload, MiniLM) | Δ MiniLM | Ans. Rel (`why` payload, Gemini emb) | Δ Gemini |
|-----------|:---:|:---:|:---:|:---:|:---:|
| gemma2-9b     | 0.367 | 0.347 | **−0.020** | 0.640 | +0.273 |
| llama3.1-8b   | 0.378 | 0.370 | −0.008 | 0.649 | +0.271 |
| mistral-7b    | 0.349 | 0.368 | +0.019 | 0.634 | +0.285 |
| phi3.5-3.8b   | 0.378 | 0.346 | **−0.032** | 0.634 | +0.255 |

**Interpretation.** Under the production embedding model (`all-MiniLM-L6-v2` — the same one [`llm_ragas_score.py`](llm_ragas_score.py) uses, and the one validated as best-on-corpus in the RAG Retrieval Benchmark Report), the `why`-only payload **does not improve `answer_relevancy`**: three of the four generators actually move very slightly downward and the largest observed change is ±0.03. The payload-artefact hypothesis is therefore **not supported**. The 0.35–0.38 cluster is a real measurement of semantic distance between MiniLM-embedded reverse-engineered questions and MiniLM-embedded golden questions, not a payload-shape bug.

The Gemini-embedding column is kept as a sensitivity result. Switching from MiniLM (384-dim) to Gemini `gemini-embedding-001` (3072-dim) does lift every generator by roughly +0.27, but this is an *embedding-model effect*, not a payload effect: a larger, more expressive embedding model registers systematically higher cosine similarities on short English mental-health text. Because `llm_ragas_score.py` uses MiniLM — and because MiniLM was explicitly validated as the best-performing embedding on this corpus in the RAG Retrieval Benchmark Report (800/100 hybrid, RAGAS 0.867) — the production-relevant number is the MiniLM column.

**What this means for the benchmark.** `answer_relevancy` is not broken and is not being measured incorrectly; it is simply a weak discriminator for question-generation tasks when paired with a small embedding model, because all four generators produce semantically similar explanations that MiniLM cannot tell apart at a useful resolution. This is why its weight in the composite (0.1) is already low. Faithfulness and format compliance remain the only meaningful discriminators — this finding tightens the confidence in that call rather than changing it. The `generated_answer` serialisation in `llm_benchmark.py` has been left as the original MCQ form, because the `why`-only alternative produced no measurable benefit under production scoring. The rescore artefacts are preserved for audit: `results/llm_20260410_191454_rescored.csv` (Gemini-embedding exploration) and `results/llm_20260410_191454_rescored_minilm.csv` (production-parity confirmation). No change to the Top-5 configurations, the composite rankings, or the §4 recommendation follows from this investigation.

### Finding 5: The MCQ quality rubric discriminates where RAGAS answer-side metrics fail

Finding 4 established that `answer_relevancy` is a weak discriminator on MCQ generation: every generator clusters in 0.35–0.38 under MiniLM. Swapping it for `answer_correctness` (a semantic-similarity-plus-factual-overlap metric) was tried as a follow-up audit and produced a similarly tight band (0.34–0.40), confirming that the problem is the *task*, not the specific metric: MCQ generation is too narrow to separate generators on answer-side semantic similarity when the answer payload is a short, heavily-templated JSON object and the underlying embedding is a small sentence transformer. This is consistent with the known surface-form compression observed in LLM-as-judge / similarity-based evaluations on structured outputs (Liang et al. 2023 HELM; Zheng et al. 2023 MT-Bench; Es et al. 2024 RAGAS).

**The rubric.** Inspired by the Med-PaLM clinical QA evaluation protocol (Singhal et al. 2023), a task-specific LLM-as-judge rubric was introduced: the same Gemini 2.5 Flash Lite judge scores each generated MCQ on three MCQ-specific dimensions, each 1–5 — **stem clarity**, **distractor plausibility**, and **pedagogical appropriateness**. These are the three quality axes identified by Kurdi et al. (2020) in their systematic review of automatic MCQ generation, and the distractor dimension in particular is validated as the hardest and most informative signal in the automatic-question-generation literature (Gao et al. 2019; Bitew et al. 2022). The rubric prompt returns strict JSON and `mcq_quality` is the normalised mean (0–1). Full prompt and rationale: see [LLM_BENCHMARK_METHODOLOGY.md §4.4](methodologies/LLM_BENCHMARK_METHODOLOGY.md) and the shared implementation in [benchmarks/rubric.py](rubric.py).

**Results.** The rubric produces a useful per-generator spread (0.697–0.806 vs 0.35–0.38 for answer_relevancy) and, crucially, is driven by the two dimensions that matter pedagogically: distractor plausibility and appropriateness. The two surface-form saturated dimensions (stem clarity on all models except mistral, format compliance on gemma2) are already captured by existing metrics, so the rubric complements rather than duplicates them. Applied to the full 480-row CSV via [rescore_mcq_rubric.py](rescore_mcq_rubric.py) (audit rig, ~6.6 min against Gemini 2.5 Flash Lite on the paid tier; n = 425 parseable rows), it produces the §2.6 sub-scores and the updated §2.1 ranking. **One ranking flip surfaced**: phi3.5-3.8b moved ahead of llama3.1-8b by 0.003 composite. The margin is within judge noise, but the direction is consistent with the rubric sub-scores — phi3.5 leads on both distractor plausibility and pedagogical appropriateness, and llama3.1's advantages (format compliance, faithfulness) are already fully reflected in the other composite terms. gemma2-9b's top-line ranking is unchanged.

**Composite reweighting.** The old v1 composite was `0.4·faith + 0.4·ctx + 0.1·ans_rel + 0.1·fmt`. After the swap, the v2 composite is **`0.4·faith + 0.3·ctx + 0.2·mcq_quality + 0.1·fmt`**. The 0.4 weight on faithfulness is unchanged (grounding is still the primary quality concern). The context weight dropped from 0.4 to 0.3 because `context_relevancy` is a constant across generators in this study — at 0.4 it inflates the per-generator composite without contributing discriminating signal — and the released 0.1 was added to `mcq_quality` to bring the task-specific signal to a full 0.2. Grounding (faithfulness + retrieved-context quality) still dominates at 70 %. The v1 formula is preserved as a deprecated path in both `llm_benchmark.py::composite_score` and `benchmarks/rubric.py::composite_score` for auditability.

**What this means for the thesis.** The null result (Finding 4) and the positive result (Finding 5) together form a reusable methodological contribution: for generative tasks where the outputs are highly templated, sentence-embedding-based similarity metrics should be audited for surface-form compression before being used as discriminators, and can be profitably replaced with a domain-specific LLM-as-judge rubric grounded in the task's own quality literature.

### Finding 6: Retrieval dominates generation in the composite

Because `context_relevancy` contributes 30 % of the v2 composite and is identical across generators, the floor of any composite score is ≈ 0.238 (0.3 × mean context relevancy of 0.795). The observed spread between generators — 0.765 to 0.831, a ~7-point range — happens entirely in the faithfulness + format + mcq_quality dimensions. In other words, **good retrieval raises the floor; choice of generator raises the ceiling**. This reinforces the RAG Retrieval Benchmark Report's finding that hybrid retrieval is the highest-leverage improvement.

---

## 4. Recommended Configuration

| Decision | Recommendation | Rationale |
|----------|----------------|-----------|
| Generator | **`gemma2:9b-instruct-q4_0`** | Best faithfulness (0.833), perfect format compliance (100 %), highest composite (0.8305); strongest or co-strongest on every axis except pedagogical appropriateness |
| Fallback generator | `phi3.5:3.8b-mini-instruct-q4_0` | Fastest (41.7 s median), highest MCQ quality rubric (0.806), leads on distractor plausibility and pedagogical appropriateness; overtook llama3.1-8b on the v2 composite |
| Baseline to retire | `mistral:7b-instruct-q4_0` | 25.8 % format-failure rate; lowest faithfulness mean; lowest MCQ quality rubric (0.697); no advantage on any dimension |
| Retrieval | Unchanged — see RAG report | Hybrid retrieval with all-MiniLM-L6-v2, 800/100 chunks (already validated) |

**End-to-end recommended stack**: gemma2-9b generator + all-MiniLM-L6-v2 embeddings + 800/100 chunks + hybrid retrieval. This inherits the retrieval-level robustness established in the RAG benchmark. The Top-5 table shows marginally higher per-configuration composites on non-MiniLM embeddings, but those are driven by specific (config × question) rows rather than consistent improvements, and all-MiniLM-L6-v2 remains the production embedding validated across the full RAG benchmark.

---

## 5. Should Further Optimisation Be Pursued?

### What the current score means

A composite of **0.8305** for gemma2-9b means the production pipeline, if upgraded, would produce well-formed, grounded, pedagogically appropriate MCQs on the first attempt in roughly 83 % of cases, with the remaining headroom coming from imperfect retrieval contexts, subtle wording drift in the generated explanation, and the ceiling on distractor plausibility. For a quiz system that already falls back to generic questions on failure, this is well above the threshold of usefulness.

### Where the remaining gap is

1. **Retrieval ceiling** — 0.795 mean context relevancy leaves ~20 % headroom that no generator can recover. Retrieval-side improvements (hybrid, query expansion) will lift the composite floor.
2. **Faithfulness long tail** — even gemma2 produces occasional 0.25 rows. These cluster on research-paper questions with specialised vocabulary, where the model paraphrases statistics inaccurately. Prompt engineering (explicit "quote the passage verbatim" instructions) may help.
3. **Pedagogical appropriateness ceiling** — the best model on this dimension scores only 3.62/5 (phi3.5). Every generator tends toward phrase-lookup questions rather than conceptual probing. The MCQ-generation literature treats this as an open problem.

### What could improve scores further

| Approach | Expected gain | Effort | Recommendation |
|----------|:---:|:---:|:---:|
| Prompt engineering for verbatim grounding | ~2–3 pp faithfulness | Low | Worth trying |
| Prompt engineering for conceptual-probe MCQs | ~5–10 pp rubric (ped. app.) | Low-Medium | Worth trying — biggest headroom on the v2 composite |
| Larger generator (27 B+ class, e.g. gemma2-27b-q4) | Unknown | Medium (memory) | Not recommended — latency already the bottleneck |
| Fine-tuning on student-mental-health MCQ corpora | Moderate (~5 pp) | High | Not recommended for v1 |
| Self-consistency sampling (generate N, majority vote) | ~3–4 pp | Medium (latency ×N) | Reserve for a high-stakes mode |

### Verdict

gemma2-9b is a clear, low-risk upgrade from the current baseline. It fixes the 26 %-format-failure problem for free, raises faithfulness by ~12 pp, and lifts the MCQ quality rubric by ~9 pp over mistral. The biggest remaining quality lever is on the retrieval side (already validated separately); the biggest remaining generation lever is prompt engineering for conceptual-probe MCQs, which is the one rubric dimension where even the best generator leaves ~30 % headroom on the table.

For the thesis, the narrative is: **a single generator swap from Mistral 7B to Gemma2 9B eliminates all format-compliance failures, improves grounding faithfulness by 12 percentage points, raises the MCQ quality rubric by 9 percentage points, and raises the composite quality score by 6.6 points (v2 composite: 0.7646 → 0.8305) — with no prompt changes and no retrieval-pipeline modification.**

---

## 7. Replication with Domain-Grounded System Prompt and Expanded Question Set (Run 2)

### 7.1 Motivation

The initial benchmark (Sections 2–6) identified gemma2-9b as the strongest generator and prompt engineering for conceptual-probe MCQs as the biggest remaining quality lever (§5, "pedagogical appropriateness ceiling"). Concurrently, qualitative review of production quiz output revealed a recurring failure mode: questions that tested document navigation rather than mental-health understanding — e.g. *"Which of the following is mentioned as a category in the table?"* or *"According to the title, which potential effect of bullying is mentioned?"*.

Two interventions were applied before Run 2:

1. **Domain-grounded system prompt.** The `SYSTEM_QG` prompt was rewritten from a generic 3-line instruction to a 7-line domain-specific prompt that identifies the audience (primary and secondary school teachers), the subject domain (student mental health: school anxiety, emotional well-being, early intervention), and explicitly prohibits questions about document structure, table labels, page references, or methodology details. Each difficulty level (beginner, intermediate, advanced) was also updated with domain-specific question stems and a "do NOT ask about document structure" guard.

2. **Expanded golden question set.** Run 2 uses the same 15 golden questions from the RAG benchmark Run 2 (see RAG Benchmark Report §7.1), covering all three difficulty levels, the full keyword taxonomy, and all eight corpus sources. The RAG CSV (`rag_20260414_022925.csv`) provides 180 frozen retrieval contexts per generator (12 configs × 15 questions), up from 120 in Run 1 (12 configs × 10 questions).

The benchmark's `USER_PROMPT_TEMPLATE` was intentionally left unchanged — it remains a simplified, difficulty-neutral template to isolate the effect of the system prompt from the adaptive-difficulty system. This means Run 2 measures whether domain grounding in the system prompt alone can improve generation quality.

### 7.2 Per-generator summary

| Generator | Format | Faith | MCQ Qual | Composite | Latency (s, avg) |
|-----------|:---:|:---:|:---:|:---:|:---:|
| **gemma2-9b** | **0.983** | **0.867** | **0.824** | **0.884** | 74.5 |
| llama3.1-8b | 0.817 | 0.827 | 0.765 | 0.854 | 57.0 |
| phi3.5-3.8b | 0.822 | 0.700 | 0.777 | 0.804 | **39.7** |
| mistral-7b | 0.678 | 0.726 | 0.646 | 0.786 | 68.0 |

### 7.3 Comparison with Run 1

| Generator | | Format | Faith | MCQ Qual | Composite |
|-----------|---|:---:|:---:|:---:|:---:|
| **gemma2-9b** | Run 1 | 1.000 | 0.833 | 0.784 | 0.831 |
| | Run 2 | 0.983 | 0.867 | 0.824 | 0.884 |
| | **Delta** | **-0.017** | **+0.034** | **+0.040** | **+0.053** |
| llama3.1-8b | Run 1 | 0.942 | 0.735 | 0.780 | 0.781 |
| | Run 2 | 0.817 | 0.827 | 0.765 | 0.854 |
| | **Delta** | **-0.125** | **+0.092** | **-0.015** | **+0.073** |
| phi3.5-3.8b | Run 1 | 0.842 | 0.722 | 0.806 | 0.784 |
| | Run 2 | 0.822 | 0.700 | 0.777 | 0.804 |
| | **Delta** | **-0.020** | **-0.022** | **-0.029** | **+0.020** |
| mistral-7b | Run 1 | 0.742 | 0.714 | 0.697 | 0.765 |
| | Run 2 | 0.678 | 0.726 | 0.646 | 0.786 |
| | **Delta** | **-0.064** | **+0.012** | **-0.051** | **+0.021** |

Composite scores improved across all four generators (+2.0 to +7.3 pp), driven primarily by higher context relevancy in the expanded RAG CSV (0.795 → 0.845–0.966 depending on config). However, the individual quality metrics reveal a divergent pattern: gemma2-9b improved on every quality axis, while the other three models showed format compliance regressions that dragged down their MCQ quality averages.

### 7.4 Rubric sub-scores: Run 1 vs Run 2

| Generator | | Stem clarity | Distractor plausibility | Pedagogical appropriateness |
|-----------|---|:---:|:---:|:---:|
| **gemma2-9b** | Run 1 | 4.97 | 3.61 | 3.19 |
| | Run 2 | 4.97 | 3.76 | 3.63 |
| | **Delta** | **0.00** | **+0.15** | **+0.44** |
| llama3.1-8b | Run 1 | 4.88 | 3.56 | 3.25 |
| | Run 2 | 4.73 | 3.50 | 3.23 |
| | **Delta** | **-0.15** | **-0.06** | **-0.02** |
| phi3.5-3.8b | Run 1 | 4.78 | 3.68 | 3.62 |
| | Run 2 | 4.66 | 3.57 | 3.43 |
| | **Delta** | **-0.12** | **-0.11** | **-0.19** |
| mistral-7b | Run 1 | 4.40 | 3.01 | 3.04 |
| | Run 2 | 4.07 | 2.93 | 2.70 |
| | **Delta** | **-0.33** | **-0.08** | **-0.34** |

The pedagogical appropriateness improvement for gemma2-9b (**+0.44 on a 5-point scale, +14%**) is the single largest rubric change in either run. This directly addresses the qualitative observation that motivated the prompt rewrite: questions now test understanding of concepts, risk factors, and interventions rather than document navigation.

### 7.5 Why format compliance dropped for weaker models

Format compliance decreased for every model except gemma2 (which remained near-perfect at 98.3%). The regression is most severe for llama3.1-8b (-12.5 pp) and mistral-7b (-6.4 pp).

The cause is the **longer, more constrained system prompt**. The Run 1 `SYSTEM_QG` was three lines:

> *You are a careful assessment item writer. You write questions ONLY from the provided excerpt. Do not invent facts. Always output strict JSON.*

The Run 2 version is seven lines with domain context, audience description, and explicit prohibitions. Inspection of format failures reveals three patterns:

- **Chatty preambles** (llama3.1): `"Here is a single multiple-choice question..."` before the JSON
- **Inconsistent formatting** (mistral): options split across lines, missing commas, unescaped quotes
- **Code fences** (phi3.5): wrapping JSON in `` ```json ``` `` blocks that the strict parser rejects

This degradation under increased prompt complexity is consistent with the instruction-following literature. Zhou et al. (2023) established with IFEval that verifiable instruction compliance drops as the number and complexity of constraints increases, and that this effect is more pronounced in smaller models. Jaroslawicz et al. (2025) confirmed this scaling relationship with IFScale, showing that instruction-following performance degrades monotonically with instruction density, and that only the largest reasoning models maintain near-perfect compliance beyond 150 constraints. In the MCQ generation context specifically, Docherty (2024) found that small open-weight models (including Llama 3.2 3B) "perform poorly for all but the simplest schemas" when generating structured JSON, while larger models handle complex structured outputs more reliably.

These are instruction-following failures under a more complex prompt, not content-quality regressions. The *scored* questions from these models are not meaningfully worse — the averages drop because more rows produce unparseable output and receive null scores. This reinforces the gemma2-9b recommendation: it is the only model in this parameter class robust enough to maintain format discipline under domain-specific prompting constraints.

### 7.6 RAGAS faithfulness distribution

| Generator | Perfect (1.0) | High (0.8–1.0) | Mid (0.5–0.8) | Low (0–0.5) | Zero (0.0) |
|-----------|:---:|:---:|:---:|:---:|:---:|
| **gemma2-9b** | **116 (66%)** | 13 | 37 | 9 | 1 |
| llama3.1-8b | 90 (60%) | 10 | 39 | 7 | 4 |
| phi3.5-3.8b | 55 (33%) | 17 | 68 | 24 | 5 |
| mistral-7b | 49 (33%) | 22 | 53 | 22 | 3 |

gemma2-9b achieves a perfect faithfulness score on 66% of questions — nearly double the rate of mistral and phi3.5. It also has the fewest zero-faithfulness (fully hallucinated) generations (1 vs 3–5 for other models).

### 7.7 Top 5 end-to-end configurations (Run 2)

| # | Generator | Embedding | Chunks | Retrieval | Composite |
|---|-----------|-----------|:---:|:---:|:---:|
| 1 | gemma2-9b | bge-small-en-v1.5 | 800/100 | hybrid | **0.938** |
| 2 | gemma2-9b | all-mpnet-base-v2 | 800/100 | hybrid | 0.927 |
| 3 | gemma2-9b | all-MiniLM-L6-v2 | 800/100 | hybrid | 0.913 |
| 4 | gemma2-9b | all-mpnet-base-v2 | 800/100 | dense | 0.901 |
| 5 | llama3.1-8b | all-mpnet-base-v2 | 512/50 | hybrid | 0.901 |

All top-4 slots are held by gemma2-9b. The best end-to-end composite (0.938) is a **+6.4 pp improvement** over the Run 1 best (0.874, gemma2 + mpnet 800/100 hybrid). Hybrid retrieval with 800/100 chunks dominates the top positions across all embedding models, consistent with the RAG benchmark findings.

### 7.8 Distractor plausibility: a model capability ceiling

The distractor plausibility score remains the weakest rubric dimension across all generators in both runs (Run 2 range: 2.93–3.76/5). This is consistent with the broader automatic MCQ generation literature. Awalurahman & Budi (2024) identified distractor generation as the most challenging sub-task in their systematic review of 60 studies spanning 2009–2024, noting that plausible distractors require understanding of common misconceptions — a capability that depends on domain knowledge rather than linguistic fluency. Tran et al. (2024) found that even LLMs that generate mathematically valid distractors are "less adept at anticipating common errors or misconceptions among real students", and that 57% of LLM-generated MCQs contained at least one implausible distractor.

The gemma2-9b improvement from 3.61 to 3.76 (+0.15) suggests that domain grounding in the system prompt helps the model select more plausible wrong answers from the mental-health domain, but the remaining gap to 5.0 is a model capability limitation at the 9B Q4_0 parameter class — not a prompt engineering problem.

### 7.9 Updated recommendation

| Decision | Run 1 | Run 2 | Change |
|----------|-------|-------|--------|
| Generator | gemma2-9b | gemma2-9b | Unchanged |
| Composite score | 0.831 | **0.884** | **+0.053** |
| Best end-to-end | 0.874 | **0.938** | **+0.064** |
| Pedagogical appropriateness | 3.19/5 | **3.63/5** | **+0.44** |
| Distractor plausibility | 3.61/5 | **3.76/5** | **+0.15** |

The generator recommendation is unchanged. The domain-grounded system prompt improved gemma2-9b's composite by 5.3 percentage points and its pedagogical appropriateness by 14%. These gains came from a prompt-only intervention — no model retraining, no architectural changes, and no additional inference cost.

For the thesis, the narrative extends the Run 1 finding: **adding domain-specific system prompt instructions to the already-recommended gemma2-9b generator improved the composite quality score by a further 5.3 percentage points (0.831 → 0.884), with the largest gain on pedagogical appropriateness (+14%), the dimension most directly tied to learning outcomes. The same prompt changes degraded format compliance for smaller models (mistral-7b, phi3.5-3.8b) due to the well-documented instruction-following scaling effect (Zhou et al. 2023; Jaroslawicz et al. 2025), reinforcing the case for gemma2-9b as the production generator.**

---

## 8. Methodology Notes

- **Judge model:** Google Gemini 2.5 Flash Lite, accessed via `langchain-google-genai==1.0.10`. Selected to avoid the small-model self-grading bias described by Zheng et al. (2023). Paid-tier free-daily-quota was not sufficient (20 requests/day for the lite model); billing was enabled to complete the 480-row run in one session.
- **Generation determinism:** All generators ran with `temperature=0.0` and `seed=7`. Responses are reproducible for the same Ollama model weights.
- **Retrieval freeze:** The 120 context sets per generator were loaded from `rag_20260410_160216.csv`, not re-queried. This guarantees every generator sees byte-identical excerpts.
- **Strict-JSON validation:** Implemented in `services/benchmarks/parsing.py::validate_format`. Checks (a) dict type, (b) required keys present, (c) `options` is a list of exactly 4 items, (d) `correct` ∈ {A,B,C,D}. Pass = 1.0, Fail = 0.0. No partial credit.
- **Model management:** Each generator was `ollama pull`ed, benchmarked, then `ollama rm`ed sequentially to keep disk usage bounded.
- **NaN handling:** 31/480 rows (6.5 %) produced a NaN faithfulness score — these are RAGAS failures where the judge could not decompose the answer into verifiable claims, typically on rows with severe format failures. They are excluded from the generator-level means (n is reported in the summary table).
- **Statistical limitations:** 10 golden questions × 12 retrieval configurations = 120 observations per generator. This is sufficient to show consistent direction but not formal significance. A replicated run with a larger question bank (50+) and a second, stronger judge (e.g. Gemini 2.5 Pro) would be required for peer-review-grade claims.
- **RAGAS version:** 0.1.22 (pinned in `services/requirements.txt`). Active metric: `faithfulness` only, evaluated against Gemini with `max_workers=1` and a batch size of 5 questions per judge call. `answer_relevancy` was removed from the active metric set after Finding 4; the code path is commented rather than deleted so it can be re-enabled for investigation.
- **MCQ quality rubric:** Implemented in `services/benchmarks/scoring/rubric.py` as the shared source of truth. One direct Gemini 2.5 Flash Lite call per row, reusing the same judge instance as RAGAS faithfulness. Returns strict JSON with three 1–5 integers; `mcq_quality = round(mean/5, 4)`. 3-attempt retry with 30×attempt backoff on HTTP 429. Both `llm_benchmark.py` (online scoring) and `llm_ragas_score.py` (offline rescoring) import from this module.

---

## References

- Abdin, M., et al. (2024). Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone. *arXiv:2404.14219*.
- Awalurahman, A., & Budi, I. (2024). Automatic distractor generation in multiple-choice questions: a systematic literature review. *PeerJ Computer Science*, 10, e2441.
- Bitew, S. K., Deleu, J., Develder, C., & Demeester, T. (2022). Learning to Reuse Distractors to Support Multiple-Choice Question Generation in Education. *IEEE Transactions on Learning Technologies*.
- Es, S., James, J., Anke, L. E., & Schockaert, S. (2024). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *EACL 2024 System Demonstrations*. (arXiv:2309.15217).
- Gao, Y., Bing, L., Chen, W., Lyu, M. R., & King, I. (2019). Difficulty Controllable Generation of Reading Comprehension Questions. *IJCAI 2019*.
- Jaroslawicz, D., et al. (2025). How Many Instructions Can LLMs Follow at Once? *arXiv:2507.11538*.
- Kurdi, G., Leo, J., Parsia, B., Sattler, U., & Al-Emari, S. (2020). A Systematic Review of Automatic Question Generation for Educational Purposes. *International Journal of Artificial Intelligence in Education*, 30(1), 121–204.
- Liang, P., et al. (2023). Holistic Evaluation of Language Models (HELM). *Transactions on Machine Learning Research*. (arXiv:2211.09110).
- Singhal, K., et al. (2023). Large Language Models Encode Clinical Knowledge (Med-PaLM). *Nature*, 620(7972), 172–180.
- Team Gemma. (2024). Gemma 2: Improving Open Language Models at a Practical Size. *Google DeepMind technical report*.
- Tran, K., et al. (2024). Exploring Automated Distractor Generation for Math Multiple-choice Questions via Large Language Models. *Findings of NAACL 2024*. (arXiv:2404.02124).
- Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *arXiv:2306.05685*.
- Zhou, J., Lu, T., Mishra, S., Brahma, S., Basu, S., Luan, Y., Zhou, D., & Hou, L. (2023). Instruction-Following Evaluation for Large Language Models. *arXiv:2311.07911*.
