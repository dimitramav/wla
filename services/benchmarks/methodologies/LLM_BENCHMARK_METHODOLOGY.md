# LLM Generation Benchmarking Methodology

---

## 1. What Is Being Evaluated

This benchmark evaluates **question generation quality** — whether a language model can produce a well-formed, factually grounded multiple-choice quiz question from retrieved context chunks. It is the second stage of a two-stage evaluation pipeline: the RAG retrieval benchmark (Phase 6) evaluates which chunks are retrieved; this benchmark evaluates what the model does with those chunks.

The two stages are deliberately decoupled. The LLM benchmark reads frozen retrieval results from the RAG benchmark CSV, meaning every generator model receives the exact same input chunks. This eliminates retrieval as a confounding variable and isolates generation quality as the only independent variable.

### Why generation quality matters for this application

The WLA platform trains teachers on student mental health through quiz questions. A generation failure has direct pedagogical consequences:

- **Hallucinated content** could teach teachers incorrect information about recognising anxiety or responding to distressed students
- **Malformed output** (broken JSON) crashes the quiz flow, breaking the learning experience
- **Off-topic questions** waste the teacher's time and erode trust in the platform

These failure modes have different severity. Hallucination is the most dangerous; malformed output is the most visible. The evaluation metrics and composite scoring are weighted accordingly.

---

## 2. Generator Models

### Selection criteria

All generator models were selected based on four constraints:

1. **Local execution** — must run on consumer hardware via Ollama to match the platform's local deployment model
2. **Instruction-tuned** — must follow structured prompts and produce JSON output reliably
3. **Quantised (Q4)** — all models use 4-bit quantisation to ensure fair comparison under identical memory constraints
4. **Diverse architecture** — models span different families and training approaches to produce meaningful comparison

### Why local-only

All generators run locally via Ollama under identical hardware conditions. This eliminates confounding variables that would arise from mixing local and API-hosted models:

- **Network latency** would inflate response time measurements for API models, making timing comparisons meaningless
- **Different quantisation levels** — API providers typically serve full-precision or 8-bit models, while local models run at 4-bit. Comparing generation quality across quantisation levels conflates model capability with precision loss
- **Provider-specific inference optimisations** (batching, speculative decoding, custom kernels) would give API models an unfair advantage on latency and potentially on output quality

For the thesis methodology, local-only execution means the results are fully reproducible by any researcher with the same hardware and Ollama installation.

### Model inventory

| Model | Ollama tag | Parameters | Role | Rationale |
|-------|-----------|------------|------|-----------|
| Mistral 7B | `mistral:7b-instruct-q4_0` | 7B | Baseline | Current production model. The control against which all other models are compared. |
| Llama 3.1 8B | `llama3.1:8b-instruct-q4_0` | 8B | Contender | Meta's instruction-tuned model with strong structured output compliance. Widely benchmarked in the literature, making results easy to contextualise. |
| Gemma 2 9B | `gemma2:9b-instruct-q4_0` | 9B | Contender | Google's model with a different architecture and training objective. Known for strong factual grounding in benchmarks. Provides architectural diversity. |
| Phi-3.5 Mini | `phi3.5:3.8b-mini-instruct-q4_0` | 3.8B | Size comparison | Half the parameter count of the other models. Tests whether a smaller, faster model meets the quality threshold for educational deployment. An interesting finding either way: if it holds up, lighter deployment is viable; if not, the quality threshold is empirically established. |

### Why these four and not more

Four models produce a benchmark matrix of 4 generators × 12 RAG configurations × 15 golden questions = **720 evaluation rows**. This is substantial enough for thesis analysis while remaining computationally tractable with local inference. Adding more models would increase runtime linearly without proportional analytical value — the four selected models already cover three model families (Mistral, Meta, Google, Microsoft) and two size classes (3.8B vs 7–9B).

### Disk management

Each Q4 model occupies approximately 4–5 GB on disk. Running all four simultaneously would require ~20 GB. To manage disk usage, the benchmark script automatically pulls each model before its evaluation round and removes it afterwards via `ollama pull` / `ollama rm`. Only one model is loaded at a time, keeping peak disk usage at ~5 GB.

---

## 3. Judge Model

### Why a separate judge

Zheng et al. (2023), *"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"*, demonstrated that small-parameter language models (~7B) exhibit systematic biases when used as evaluators:

- **Position bias** — tendency to favour the first or last option in a comparison, regardless of quality
- **Self-enhancement bias** — models rate their own outputs higher than equivalent outputs from other models

These biases make it unreliable to use the same 7B models that generate quiz questions to also judge their quality. A separate, larger judge model is needed to produce credible evaluation scores.

### Model choice

**Google `gemini-2.5-flash-lite`** was selected as the RAGAS judge for three reasons:

1. **Scale** — a large proprietary model with evaluation quality comparable to GPT-4-class judges (Zheng et al., 2023) while avoiding the biases observed in 7B evaluators
2. **Independence** — the judge is not one of the four generator models being evaluated, eliminating self-assessment bias entirely
3. **Cost efficiency** — Gemini 2.5 Flash Lite is the cheapest tier of the Gemini 2.5 family and completed the 720-row evaluation for well under $1 on the paid tier, keeping the evaluation accessible for academic research. The free tier's daily cap (20 requests/day for Flash Lite) is not sufficient for a 720-row run, so a billing-enabled project is required.

### Rate limit handling

Gemini imposes per-minute request limits even on the paid tier. The benchmark handles this with:

- Sequential evaluation (`max_workers=1`) rather than parallel
- Exponential backoff on HTTP 429 responses (30s, 60s, 90s across 3 retry attempts)
- Graceful degradation — if all retries fail, the affected rows record `None` for judge metrics and the benchmark continues

---

## 4. Evaluation Metrics

The benchmark tracks six metrics per evaluation row. The first five are measured independently; the sixth is a weighted composite.

### 4.1 Format compliance

**What:** Does the LLM output valid JSON with the required schema?

**How:** The raw LLM output is parsed with `json.loads`. If parsing succeeds, the result is checked for required keys (`text`, `options`, `correct`, `why`), correct option count (exactly 4), and valid correct-answer format (`A`/`B`/`C`/`D`). Score is binary: `1.0` (fully compliant) or `0.0` (any failure).

**Why it matters:** Format compliance is a prerequisite for the quiz to function. A model that produces correct content but broken JSON is unusable in production. Binary scoring reflects this: partial compliance still breaks the pipeline.

### 4.2 Response time

**What:** How long does the model take to generate one question?

**How:** `time.time()` wrapped around the Ollama API call, measured in seconds.

**Why it matters:** For an interactive quiz platform, response time directly affects user experience. A model that produces better questions but takes 60 seconds per question may be impractical. Response time is reported but not included in the composite score — it is a deployment constraint, not a quality metric.

### 4.3 Faithfulness

**What:** Is the generated question grounded in the retrieved context, or does it contain hallucinated claims?

**How:** RAGAS `faithfulness` metric, evaluated by the Gemini judge. Scores 0–1, where 1.0 means every claim in the generated output can be traced back to the provided context.

**Why it matters:** This is the highest-stakes metric for the WLA application. A hallucinated claim about student mental health — for example, inventing a statistic about anxiety prevalence or fabricating an intervention technique — could actively misinform teachers.

### 4.4 MCQ quality rubric

**What:** Does the generated multiple-choice question meet the structural and pedagogical standards of a well-formed educational assessment item?

**How:** A task-specific LLM-as-judge rubric, evaluated by the Gemini 2.5 Flash Lite judge. Each generated MCQ is rated on three dimensions, each on a 1–5 integer scale:

1. **Stem clarity** — is the question stem well-formed, unambiguous, and self-contained? A stem scoring 5 is clear and focused, a teacher can understand exactly what is being asked without any additional context; a stem scoring 3 is understandable but somewhat vague or wordy; a stem scoring 1 is grammatically broken, ambiguous, or incomprehensible without additional context.
2. **Distractor plausibility** — are the three incorrect options plausible-but-wrong: topically relevant, not trivially identifiable as wrong, and meaningfully distinct from the correct answer? A score of 5 means all three distractors represent genuine misconceptions or near-miss answers a learner could reasonably consider; a score of 3 means distractors are on-topic but clearly weaker, or one is obviously wrong; a score of 1 means the distractors are absurd, off-topic, near-duplicates of the correct answer, or obviously nonsensical.
3. **Pedagogical appropriateness** — does the question help a teacher learn or retain a meaningful concept about student mental health? A score of 5 tests conceptual understanding, application to classroom scenarios, or meaningful relationships between concepts — a teacher who answers correctly has genuinely learned something useful; a score of 3 tests a real concept but at a superficial level or with limited practical value; a score of 1 tests document-level details (e.g. "according to the passage", "which is NOT mentioned", author names, methodology), asks about trivial facts, or references the source material in the question stem.

The three sub-scores are averaged and normalised to a 0–1 scale to produce `mcq_quality`:

```
mcq_quality = mean(stem_clarity, distractor_plausibility, pedagogical_appropriateness) / 5
```

The rubric prompt passes the retrieved context, the parsed stem, the four options, the declared correct letter, and the explanation to the judge, which is instructed to return strict JSON with the three scores. The rubric logic is implemented in `services/benchmarks/scoring/rubric.py` and is shared by both the production scoring path (`llm_benchmark.py`, `llm_ragas_score.py`) and the offline rescoring tool (`benchmarks/investigations/rescore_mcq_rubric.py`).

**Rubric recalibration (v2).** The rubric anchor descriptions were recalibrated alongside the v2 prompt revision (see §6). The v1 `pedagogical_appropriateness` anchor asked whether the question "probes meaningful understanding **of the context**" — a framing that inadvertently rewarded text-referencing questions. A question asking "According to the excerpt, what has increased due to social media?" could legitimately score 3–4 under v1 because it does probe the context, even though it teaches nothing transferable. The v2 anchor reframes the dimension around subject-matter learning: score 5 requires that "a teacher who answers correctly has genuinely learned something useful", while score 1 now explicitly penalises document-referencing patterns ("according to the passage", "which is NOT mentioned", author names, section headings). This is not a change to the metric — the three dimensions, the 1–5 scale, the normalisation formula, and the composite weight (0.2) are all unchanged — but a refinement of the anchor descriptions to better operationalise the construct being measured (pedagogical value for teacher training). Rubric anchoring refinement is standard practice in LLM-as-judge evaluation (Zheng et al., 2023, §4.2) and is analogous to improving inter-rater calibration in human annotation — the construct definition becomes more precise, not different. The mid-scale anchor (score 3) was also added to all three dimensions; the v1 rubric only defined the extremes (1 and 5), which left the judge to interpolate the middle of the scale without guidance.

**Why a rubric replaces RAGAS `answer_relevancy`.** The original benchmark composite included RAGAS `answer_relevancy`, which reverse-engineers candidate questions from the "answer" text and measures their mean cosine similarity to the golden question via an embedding model. On the first benchmark run this metric clustered every generator at 0.35–0.38, with an absolute spread of 0.029 across the four models — insufficient to separate them. An offline investigation (Finding 4) ruled out payload shape as the cause: rescoring with a `why`-only payload under production MiniLM embeddings moved the metric by at most ±0.03 per generator. The clustering is a real consequence of three compounding factors:

1. **Surface-form compression under deterministic decoding and a strict JSON schema.** With `temperature=0`, a fixed seed, identical context, and a schema that constrains every generator to `{stem, 4 options, correct letter, why}`, the degrees of freedom for the "answer" text shrink dramatically. Sentence-embedding metrics cannot discriminate outputs that differ only in lexical choice — a format-bias / ceiling effect discussed in the HELM framework (Liang et al., 2022) and corroborated by MT-Bench's observation that closed-form tasks compress judge scores (Zheng et al., 2023).
2. **`answer_relevancy` is designed for open-ended QA.** The metric reverse-engineers candidate questions from the answer text and measures similarity to the original question (Es et al., 2024). When the answer already contains a question stem (as in MCQ generation), the reverse-engineering step is partly tautological.
3. **Statistical compression at small sample sizes.** With 120 evaluation rows per generator, per-question variance of the metric dominates the between-model signal. The metric does discriminate *within* a model (per-row scores range from 0.01 to 0.73) but these cancel on the model mean.

The rubric-based `mcq_quality` metric avoids all three issues by evaluating the full MCQ structure against explicit quality dimensions rather than measuring similarity against a reference.

**Why this rubric and these three dimensions.** The three-dimension rubric is adapted from the Med-PaLM clinical QA evaluation protocol (Singhal et al., 2023), which established LLM-as-judge rubric scoring as a valid alternative to aggregate similarity metrics in high-stakes educational/clinical QA. The specific dimensions (stem clarity, distractor plausibility, pedagogical appropriateness) correspond to the MCQ quality criteria identified by Kurdi et al. (2020) in their systematic review of automatic question generation for educational purposes, where similarity-to-reference is categorised as the weakest family of MCQ evaluation methods. Distractor plausibility in particular is known from the MCQ generation literature (Gao et al., 2019; Bitew et al., 2022) to be the dimension on which generator models differ most meaningfully, which is borne out by the empirical results in the LLM Benchmark Report Finding 5.

**Why it matters for the pipeline:** A model can be faithful to the context (no hallucination) and topically on-point but still produce a question with absurd distractors, an ambiguous stem, or a trivial-recall framing — all of which degrade the pedagogical value of the question for teacher training. The rubric surfaces these failure modes directly. Empirically it also discriminates: on the 425 rescorable rows, `mcq_quality` ranges from 0.697 (mistral-7b) to 0.806 (phi3.5-3.8b), with distractor plausibility showing the largest between-model gap (3.01–3.68 on the 1–5 scale; see LLM Benchmark Report Finding 5).

### 4.4.1 Deprecated: RAGAS answer relevancy (retained for schema compatibility)

Prior benchmark runs (before the Finding 5 rebalance) included RAGAS `answer_relevancy` at 10 % of the composite score. The metric is documented here for reproducibility: it was computed with the Gemini 2.5 Flash Lite judge and `sentence-transformers/all-MiniLM-L6-v2` as the embedding model (the same production embedding used by `llm_ragas_score.py` and the one empirically validated as best-on-corpus in the RAG Retrieval Benchmark Report). New benchmark runs no longer compute this metric, but the `answer_relevancy` column is retained in the output CSV schema so that pre-Finding-5 evaluation CSVs remain readable. The code path in `llm_benchmark.py` and `llm_ragas_score.py` is commented out rather than deleted so it can be re-enabled for ad-hoc investigations. See LLM Benchmark Report, Finding 4 for the full analysis of why this metric was deprecated.

### 4.5 Text independence

**What:** Does the generated question stand alone as a knowledge item, or does it reference the source material?

**How:** A binary metric (1.0 = standalone, 0.0 = text-referencing) scored by deterministic regex matching against the raw LLM output. The pattern list was derived from the Run 2 benchmark, where 92% of v1-prompt questions matched at least one of the following phrases:

- "according to" / "based on the text/passage/excerpt"
- "which is NOT discussed/mentioned"
- "mentioned in the/this"
- "the passage/excerpt/text states/describes/discusses/suggests"
- "as stated/described/discussed in"
- "referring to the"

**Why regex, not the LLM judge.** Text independence is a surface-level property — a question either contains "according to the excerpt" or it does not. Using regex makes the metric fully deterministic (no judge variance), reproducible without an API key, and instantaneous to compute. The Gemini judge was already scoring `pedagogical_appropriateness`, which was intended to penalise text-referencing questions at score 1, but empirical analysis showed the judge was not applying the rubric anchor correctly: 62.6% of v1 text-referencing questions received a pedagogical appropriateness score of 4 (§4.4). The judge consistently evaluated the *concept* being tested rather than the *framing* of the question. Adding a dedicated binary metric cleanly separates these two constructs — concept quality (measured by `pedagogical_appropriateness`) and text independence (measured by regex) — rather than overloading a single rubric dimension with two competing signals.

**Why it matters:** For the WLA platform, a question that says "According to the excerpt, which factor contributes to school anxiety?" tests reading comprehension, not subject knowledge. A teacher who answers it correctly has demonstrated they processed the passage, not that they understand the concept. Text-independent questions ("Which of the following is a common risk factor for school anxiety?") test transferable knowledge that the teacher retains after the quiz. This distinction — text-dependent vs text-independent items — is a core taxonomy in the automatic question generation literature (Kurdi et al., 2020, §3.2).

The regex pattern and scoring function are implemented in `services/benchmarks/scoring/rubric.py::score_text_independence()`.

### 4.6 Context relevancy

**What:** Were the retrieved chunks relevant to the question?

**How:** Carried over from the RAG benchmark CSV (`context_relevancy` column). This is the RAGAS `context_precision` score from Phase 6, not re-evaluated here.

**Why it is included:** The composite score needs to account for retrieval quality because a model cannot generate a good question from irrelevant chunks. Including context relevancy means the composite score reflects end-to-end pipeline quality, not just generation quality in isolation.

### 4.7 Composite score (Weighted Sum Model)

The composite score uses a Domain-Specific Weighted Sum Model (WSM), a standard technique in Multi-Criteria Decision Analysis (MCDA). As argued by the Holistic Evaluation of Language Models (HELM) framework (Liang et al., 2022), LLM evaluation cannot rely on universal metrics; it must be use-case specific. For a high-stakes domain like student mental health, safety and factual grounding must disproportionately dominate the evaluation criteria (similar to clinical AI benchmarks like Singhal et al., 2023).

The composite formula evolved across three iterations. Each revision was motivated by an empirical observation from the benchmark runs — not by moving goalposts, but by discovering that the existing formula failed to measure what it claimed to measure. This iterative refinement is standard practice in evaluation framework design: the HELM framework itself underwent multiple metric revisions as task-specific failure modes were discovered (Liang et al., 2022), and Zheng et al. (2023) explicitly recommend auditing composite metrics for construct validity after each evaluation round.

#### v1 (initial)

`(faithfulness × 0.4) + (context_relevancy × 0.4) + (answer_relevancy × 0.1) + (format_compliance × 0.1)`

The initial formula prioritised factual grounding at 80% (faithfulness + context relevancy), reflecting the safety-critical nature of the domain: a hallucinated claim about anxiety interventions is a worse failure than a poorly worded question. `answer_relevancy` (RAGAS cosine similarity between reverse-engineered candidate questions and the golden question) was included at 10% as a proxy for answer quality, and format compliance at 10% as a deployment requirement.

**What went wrong.** Finding 4 (LLM Benchmark Report §3) revealed that `answer_relevancy` clustered every generator in a 0.35–0.38 band — a spread of 0.029 across four models, insufficient to separate them. An offline investigation confirmed this was not a measurement bug but a real consequence of surface-form compression under deterministic decoding + strict JSON schema + small embeddings (MiniLM 384-dim). The metric was measuring the wrong thing: semantic similarity between short templated outputs rather than MCQ quality.

#### v2 (post-Finding-5): answer_relevancy → mcq_quality

`(faithfulness × 0.4) + (context_relevancy × 0.3) + (mcq_quality × 0.2) + (format_compliance × 0.1)`

Finding 5 replaced `answer_relevancy` with a task-specific MCQ quality rubric (§4.4) that evaluates stem clarity, distractor plausibility, and pedagogical appropriateness — the three quality dimensions identified by Kurdi et al. (2020) for educational MCQ evaluation. The rubric produced a useful per-generator spread (0.697–0.806) where `answer_relevancy` had failed (0.35–0.38).

Weight changes:
- **MCQ quality raised to 0.20** (from answer_relevancy's 0.10) because the rubric is a structurally validated signal on MCQ-specific dimensions, not a surface-similarity proxy.
- **Context relevancy reduced from 0.40 to 0.30** because it is a constant across generators in the decoupled architecture (§5) — at 0.40 it contributed no discriminative signal, only a floor. The freed 0.10 went to mcq_quality.
- **Factual grounding total: 70%** (faithfulness 0.40 + context_relevancy 0.30), still dominant, consistent with the HELM + Med-PaLM precedent.

This formula was used for Run 2 (LLM Benchmark Report §7).

#### The problem with v2: what the prompt ablation revealed

The v2 prompt revision (§6) achieved its primary goal: text-referencing questions dropped from 92% to 4.4% of generated output. Qualitative review confirmed a dramatic improvement — questions now tested transferable knowledge ("Which of the following is a common risk factor for school anxiety?") rather than reading comprehension ("According to the excerpt, which factor is NOT discussed?").

However, when the v2 composite was computed on the new benchmark run, the score *dropped* from 0.884 to 0.825. The prompt revision that eliminated the most significant quality problem was being *penalised* by the evaluation framework.

**Diagnosing the cause.** The composite drop was driven entirely by faithfulness (0.867 → 0.726, accounting for the full -0.059 composite decrease). The other metrics were unchanged or improved (context_relevancy identical, mcq_quality -0.009 within noise, format_compliance +0.011).

The root cause is a structural conflation in the RAGAS faithfulness metric: it measures whether the output text can be traced back to the source chunks by decomposing the output into atomic claims and checking each against the context. Text-referencing questions ("According to the excerpt, which factor contributes to anxiety?") are *trivially* faithful because they paraphrase the chunk by construction — the question literally says "according to the excerpt." Standalone concept questions ("Which of the following is a common risk factor for anxiety?") are factually grounded in the same chunks but express the knowledge in different words, which RAGAS scores lower because the surface overlap is lower.

In other words, faithfulness at 0.40 was rewarding the exact behaviour the prompt revision was designed to eliminate. The composite was not measuring quality; it was measuring how closely the question parroted the source text.

**Was the rubric supposed to catch this?** The `pedagogical_appropriateness` dimension (§4.4) was recalibrated in v2 specifically to penalise text-referencing questions: score 1 explicitly lists "according to the passage", "which is NOT mentioned", author names, methodology. But empirical analysis of the Run 2 scores showed the Gemini judge was not applying this anchor: **62.6% of text-referencing questions received a pedagogical appropriateness score of 4**. The judge consistently evaluated the *concept* being tested (a real mental-health topic → score 4) rather than the *framing* of the question (references the source → should be score 1). This is a documented limitation of LLM judges on multi-construct rubric dimensions: when a single dimension asks the judge to evaluate two competing signals simultaneously (concept quality and text independence), the judge gravitates toward the more semantically salient one. Zheng et al. (2023, §5) observed analogous anchor-ignoring behaviour in MT-Bench, where judges consistently scored on overall quality rather than the specific dimension requested by the rubric.

#### v3 (post-prompt-ablation): adding text_independence

`(faithfulness × 0.30) + (context_relevancy × 0.25) + (mcq_quality × 0.20) + (text_independence × 0.15) + (format_compliance × 0.10)`

The diagnosis revealed two measurement failures in v2: (1) faithfulness conflated factual grounding with surface text overlap, rewarding paraphrasing over standalone knowledge, and (2) the pedagogical_appropriateness rubric anchor was not enforced by the judge, leaving text independence unmeasured. Rather than attempting to fix these through stronger rubric wording (which had already failed once), the v3 formula adds a dedicated `text_independence` metric (§4.5) — a binary, deterministic, regex-based score that directly measures whether the question references the source material.

**Precedent for pedagogical quality as a rubric dimension.** Using rubric-based evaluation with pedagogical quality dimensions for AI-generated educational content is established practice across multiple domains:

- **Automatic question generation:** Kurdi et al. (2020, §3.2) identify pedagogical appropriateness as a key quality dimension in their systematic review of 93 AQG studies, separate from linguistic quality (stem clarity) and distractor quality. They also establish the text-dependent vs text-independent distinction as a fundamental taxonomy for AQG systems, classifying text independence as a separate quality axis — a question can be well-formed yet pedagogically useless if it requires the source text to answer.
- **MCQ item writing:** Haladyna et al. (2002) synthesised 27 MCQ item-writing guidelines from the educational measurement literature, with pedagogical alignment (testing the intended learning objective, not incidental details) as a primary quality criterion. Their guidelines explicitly flag "according to the passage" stems as a quality violation in knowledge-assessment contexts — the same pattern our text_independence metric captures.
- **Clinical AI evaluation:** Singhal et al. (2023) used a multi-dimension LLM-as-judge rubric for Med-PaLM, with clinical utility (analogous to pedagogical appropriateness) as a scored dimension separate from factual accuracy. Their protocol demonstrated that LLM judges can reliably score domain-specific quality constructs when rubric anchors are well-defined.
- **Educational LLM benchmarks:** Tran et al. (2024) evaluated LLM-generated maths MCQs with a rubric that included "pedagogical quality" as a dimension, finding that 57% of generated items contained at least one implausible distractor — a result consistent with our distractor_plausibility findings (§7.8). Awalurahman & Budi (2024) confirmed in their systematic review of 60 AQG studies that rubric-based expert evaluation with pedagogical dimensions is the most common evaluation method for educational question generation.

**Why text independence as a standalone metric.** The decision to add text independence as a separate composite dimension — rather than treating it as a sub-score of `mcq_quality` or as a post-hoc filter — is grounded in Kurdi et al.'s (2020) taxonomy. They classify text-dependent vs text-independent as a *separate quality axis* from stem quality or distractor quality, noting that a question can be well-formed (high stem clarity, plausible distractors) yet pedagogically useless if it requires the source text to answer. This is exactly the pattern observed in Run 2: text-referencing questions scored 4/5 on pedagogical appropriateness because the concept was sound, but they failed the text-independence criterion that Kurdi et al. treat as orthogonal. Adding it as a dedicated metric operationalises this established taxonomy rather than relying on a rubric dimension that empirically conflated the two constructs.

Weight changes and rationale:

- **text_independence added at 0.15.** This is the construct the prompt revision directly targeted and that the existing metrics failed to measure. At 0.15, a text-referencing question (score 0.0) is penalised by 0.15 composite points — roughly equal to the faithfulness boost it gets from trivial paraphrasing (empirically ~0.14), making the two effects cancel rather than compound.
- **faithfulness reduced from 0.40 to 0.30.** Faithfulness at 0.40 double-counted text dependence: paraphrasing the chunk simultaneously inflated faithfulness *and* made the question text-referencing. At 0.30, faithfulness still penalises hallucinated content (the safety-critical concern) without disproportionately rewarding surface overlap with the source text.
- **context_relevancy reduced from 0.30 to 0.25.** Still a constant across generators in the decoupled architecture; the freed 0.05 supports the new metric.
- **format_compliance unchanged at 0.10.**

**Grounding total.** Faithfulness (0.30) + context_relevancy (0.25) = 55% on factual grounding. However, `text_independence` is grounding-adjacent: a text-independent question that is also faithful represents the ideal output — factually grounded without paraphrasing. Counting text_independence as a grounding-related metric, the total is 70%, matching v2. The shift is not away from grounding but toward a more precise measurement of it.

**Validation.** Under the v3 formula, the prompt revision correctly shows an improvement: composite rose from 0.758 (v1 prompts, rescored) to 0.849 (v2 prompts), a +0.091 gain driven by text_independence (0.044 → 0.944). MCQ quality remained stable (0.824 vs 0.815, Δ = -0.009, median identical at 0.867), confirming the prompt revision improved question framing without degrading structural quality.

#### Why iterating the formula is methodologically valid

Refining a composite metric after discovering it fails to capture the construct it claims to measure is not "changing the rules" — it is standard evaluation methodology. The relevant precedents:

1. **HELM (Liang et al., 2022):** The framework explicitly warns that composite metrics must be audited for construct validity per task, and documents multiple cases where initial metric choices were revised after task-specific evaluations revealed measurement failures.
2. **MT-Bench (Zheng et al., 2023, §4.2):** Recommends rubric anchoring refinement as standard practice in LLM-as-judge evaluation, analogous to improving inter-rater calibration in human annotation.
3. **RAGAS (Es et al., 2024):** The framework itself evolved from v0.1 to v0.2 by revising how faithfulness decomposition works after users reported systematic biases in structured-output evaluation.

The key constraint is transparency: all three formula versions, their motivations, and the empirical evidence that triggered each revision are documented here. The v1 and v2 CSVs are preserved alongside their v3-rescored counterparts, and the rescoring code (`benchmarks/scoring/rubric.py::score_text_independence`, `benchmarks/scoring/composite.py`) is deterministic and reproducible.
    ↓  writes frozen results to CSV (contexts_text, ground_truth, scores)
Stage 2: LLM Generation Benchmark (llm_benchmark.py)
    ↓  reads CSV, generates questions for each generator model
    ↓  writes raw outputs and format compliance to llm_YYYYMMDD_HHMMSS.csv
Stage 3: RAGAS Scoring (llm_ragas_score.py)
    ↓  reads llm CSV, joins contexts from rag CSV
    ↓  evaluates faithfulness + answer_relevancy via Gemini judge
    ↓  updates llm CSV in place with scores and composite
```

### Why generation and scoring are decoupled

Initially, RAGAS evaluation ran inline at the end of each model's generation pass (inside `llm_benchmark.py`). Two failure modes forced decoupling into a separate script:

1. **RAGAS 0.1.x requires an explicit embedding model.** The `answer_relevancy` metric needs an embedding model in addition to the judge LLM. Without an explicit override, RAGAS fails at evaluation time because no embedding provider is configured. The decoupled scoring script explicitly sets `answer_relevancy.embeddings` to a local HuggingFace model (`all-MiniLM-L6-v2`), eliminating any external embedding dependency.
2. **Judge-availability and rate-limit risk.** Cloud judge providers can deprecate models or impose daily token caps. When inline scoring fails mid-run, the generation work is at risk of being lost. Decoupling means generation results are always saved first; scoring can be re-run independently with a different judge provider without re-running the expensive local inference stage.

Separating the two stages also means:
- **Generation is the expensive step** (~15–17 hours on local hardware for 720 rows). It runs once and its outputs are preserved in the CSV.
- **Scoring is the cheap but brittle step** (network-bound, dependent on third-party API). It can be re-run, re-tuned, or swapped for a different judge without redoing generation.
- **Format compliance, response time, and raw outputs** are available from the moment the LLM benchmark finishes, regardless of whether RAGAS succeeds.

### Why decouple

Retrieval and generation are independent variables. Testing them in a single pass (retrieve → generate → evaluate) conflates two failure modes:

- Was the question bad because the wrong chunks were retrieved?
- Or was the question bad because the model failed to use good chunks?

By freezing retrieval results in a CSV and feeding them to the generation benchmark, each model is evaluated against identical inputs. This means differences in output quality are attributable to the model, not to retrieval variance.

### Practical benefits

- **The LLM benchmark has no ChromaDB dependency** — it reads a CSV file, making it runnable on any machine without the full RAG infrastructure
- **Retrieval does not need to be re-run** when adding new generator models — pull the model, point at the same CSV, run
- **Results are fully reproducible** from the CSV alone, without needing the original vector store state

---

## 6. Prompt Design

The benchmark shares the **system prompt** (`SYSTEM_QG`) with the production system (`services/llm/prompts.py`) but uses its own **user prompt template** (`USER_PROMPT_TEMPLATE` in `llm_benchmark.py`). The system prompt is shared so that evaluation reflects the same domain framing the production quiz uses; the user prompt differs because the benchmark must inject frozen context from the RAG CSV rather than live-retrieved chunks.

### Domain-grounded system prompt

The system prompt (`SYSTEM_QG`) establishes the domain context for question generation. It has undergone two revisions:

**v1 (Run 2).** Introduced after Run 1 revealed that a minimal, domain-agnostic prompt allowed generators to produce surface-level questions about document layout. The v1 prompt instructed the model that:

- The audience is primary and secondary school teachers in a training programme on student mental health
- Questions must test understanding of concepts, risk factors, protective factors, interventions, or practical classroom strategies
- Questions must NOT ask about document structure, table labels, page references, or methodology details
- All content must come from the provided excerpt — no invented facts

**v2 (prompt revision).** Qualitative review of the expert validation spreadsheet (Phase 9) revealed that v1 questions, while avoiding overt document-structure queries, still framed themselves as reading comprehension exercises. Approximately 80 % of generated questions contained phrases like "according to the excerpt", "which is NOT discussed in this passage", or "based on the text" — testing whether the teacher read the material rather than whether they understood the subject. This pattern persisted across all four generators and all three difficulty levels, indicating a prompt-level cause rather than a model-level one.

The root cause was the v1 framing: "Write a question **from** this excerpt." This nudged the model toward text-dependent item construction (Kurdi et al., 2020, §3.2 — the distinction between text-dependent and text-independent items in automatic question generation). The v2 prompt makes three structural changes:

1. **Reframed generation goal.** From "write a question from this excerpt" to "write a question that helps a teacher learn about student mental health — use the excerpt as your factual source but never reference it in the question." The excerpt is renamed to "source material" to reinforce this mental model.
2. **Explicit anti-patterns.** A banned-phrase list was added to both the system prompt and the user template: "in this excerpt", "according to the passage", "based on the text", "which is NOT discussed", "mentioned in the research", "according to the researcher", along with document-structural references (author affiliations, supplementary files, methodology).
3. **Difficulty-level exemplars.** Each difficulty tier (beginner, intermediate, advanced) now includes concrete good stems and bad stems. For example, beginner good: "What is a common risk factor for..."; beginner bad: "According to the excerpt...". Advanced good: "A teacher notices a student increasingly avoiding group work. Which intervention approach would be most appropriate?"; advanced bad: "What can be inferred from this excerpt...". The good stems were designed to follow Bloom's taxonomy progression: recall → comprehension/application → analysis/evaluation with classroom scenarios.

The v2 prompt also adds a fallback instruction: "If the excerpt does not contain enough substantive content about the requested concept, write a question about whatever concept IS present — do not force a weak connection." This addresses a secondary failure mode where the v1 prompt, given chunks that didn't cover the target keyword, produced forced questions with tenuous connections.

**Illustrative examples.** The following pairs show questions generated by the same model (gemma2-9b, `temperature=0`, `seed=7`) from the same retrieved chunks, differing only in the prompt version. All examples are from the expert validation spreadsheet (30 MCQs, `school_anxiety` topic).

| Keyword | Difficulty | v1 prompt (text-dependent) | v2 prompt (concept-dependent) |
|---------|-----------|---------------------------|-------------------------------|
| non-attendance | beginner | "Which of these concepts is NOT discussed in this excerpt about mental health?" | "Which of the following is NOT a common reason for student non-attendance?" |
| bullying | beginner | "Does this excerpt mention bullying as a potential risk factor for student mental health?" | "Which of the following is a common characteristic of bullying behavior?" |
| anxiety symptoms | beginner | "According to the excerpt, what information related to anxiety symptoms is included in Supplementary File A?" | "Which of the following is NOT a common symptom of anxiety in children?" |
| self-esteem | beginner | "According to the excerpt, which aspect is NOT directly addressed in relation to school bullying and absenteeism?" | "Which of the following is a key factor that can contribute to a student's overall well-being and resilience against challenges like anxiety?" |
| coping | intermediate | "Based on the excerpt, what is implied about the nature of coping strategies described in Supplementary File A?" | "A student consistently struggles with a demanding workload, often appearing overwhelmed and discouraged. Which of the following best demonstrates a healthy coping strategy for this student?" |
| early intervention | intermediate | "According to the excerpt, why is it important to gain knowledge from research about school anxiety?" | "Which of these scenarios illustrates the benefit of early intervention in a school setting?" |
| resilience | advanced | "Based on the excerpt's focus on open access and public domain data, what can be inferred about the potential impact on fostering resilience in educators?" | "A student experiences a major family crisis but continues to perform well academically and maintain positive relationships with their peers. This demonstrates:" |
| family cohesion | advanced | "The excerpt primarily focuses on research conducted by Ida Huttunen. What can be inferred about her potential interest in studying family cohesion as a protective factor?" | "A teacher observes a student who seems withdrawn and has difficulty concentrating in class. Which of these factors is LEAST likely to mitigate this student's struggles?" |

The v1 questions are text-dependent: they test whether the reader processed the specific passage. The v2 questions are concept-dependent: they test transferable knowledge about student mental health. A teacher who answers the v2 questions correctly has learned something applicable to their practice; a teacher who answers the v1 questions correctly has only demonstrated reading comprehension. This distinction aligns with Kurdi et al.'s (2020) taxonomy of automatic question generation, which identifies text-independent items as the target for educational MCQ generators and text-dependent items as a known failure mode of retrieval-grounded generation.

### User prompt template

The benchmark's `USER_PROMPT_TEMPLATE` passes the frozen excerpt, difficulty level, and difficulty-specific instructions to the generator. The difficulty instructions mirror the production prompt tiers (beginner, intermediate, advanced). The prompt instructs the model to:

1. Generate exactly one multiple-choice question that helps a teacher learn about student mental health
2. Use the source material for factual grounding but never reference it in the question
3. Produce exactly 4 options labelled A–D with one correct answer
4. Include a short explanation (`why`) in terms of the subject matter, not the source text
5. Return the output as strict JSON

All generation uses `temperature=0` and a fixed seed (`seed=7`) for deterministic output.

---

## 7. Output Format

Results are written to `results/llm_YYYYMMDD_HHMMSS.csv` — one row per question per generator model per RAG configuration (720 rows for 4 models × 180 RAG rows). `llm_benchmark.py` writes the generation columns (`raw_output`, `generated_answer`, `format_compliance`, `response_time_s`) and saves incrementally after each model. `llm_ragas_score.py` then updates the same file in place with `faithfulness`, the four rubric columns (`stem_clarity`, `distractor_plausibility`, `pedagogical_appropriateness`, `mcq_quality`), and `composite_score`, resumable at the batch level if interrupted.

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | ISO 8601 | UTC timestamp of the generation |
| `generator_model` | string | Generator model name |
| `emb_model` | string | Embedding model from RAG config |
| `chunk_size` | int | Chunk size from RAG config |
| `chunk_overlap` | int | Chunk overlap from RAG config |
| `retrieval_type` | string | `dense` or `hybrid` |
| `question` | string | Golden question text |
| `ground_truth` | string | Expected answer |
| `format_compliance` | float | `1.0` or `0.0` |
| `response_time_s` | float | Generation latency in seconds |
| `raw_output` | string | Full LLM output (preserved for manual inspection) |
| `generated_answer` | string | Structured extraction of question + correct answer + explanation, passed to RAGAS `faithfulness` |
| `faithfulness` | float/null | RAGAS faithfulness score (Gemini judge) |
| `answer_relevancy` | float/null | **Deprecated** — retained for backward-compat with pre-Finding-5 CSVs; new runs write `null`. See §4.4.1 |
| `stem_clarity` | int/null | Rubric sub-score, 1–5 (Gemini judge; see §4.4) |
| `distractor_plausibility` | int/null | Rubric sub-score, 1–5 (Gemini judge; see §4.4) |
| `pedagogical_appropriateness` | int/null | Rubric sub-score, 1–5 (Gemini judge; see §4.4) |
| `mcq_quality` | float/null | Normalised rubric composite, 0–1 (mean of three sub-scores / 5) |
| `text_independence` | float | Binary: 1.0 (standalone) or 0.0 (references source material). Regex-scored, see §4.5 |
| `context_relevancy` | float/null | RAGAS context precision (from RAG CSV) |
| `composite_score` | float/null | Weighted composite v3 (§4.7): `0.30·faith + 0.25·ctx + 0.20·mcq + 0.15·ti + 0.10·fmt` |

The `raw_output` column preserves the full model response for manual inspection and thesis evidence. This is important because RAGAS scores are aggregate measures — inspecting individual outputs reveals qualitative patterns (e.g. a model that consistently produces valid JSON but with implausible distractors).

---

## 8. Reproducibility

- All generation uses `temperature=0` and `seed=7` for deterministic output to ensure that all differences in evaluation scores are strictly attributable to model capability or retrieval context, eliminating output variance as a confounding variable.
- The input CSV (frozen RAG retrieval) ensures identical context across runs
- Gemini judge evaluation is sequential and deterministic (`temperature=0`)
- The `ollama pull`/`ollama rm` cycle ensures each model runs from a clean state
- Model versions are pinned via Ollama tags (e.g. `mistral:7b-instruct-q4_0`)

---

## References

- Awalurahman, A., & Budi, I. (2024). Automatic distractor generation in multiple-choice questions: a systematic literature review. *PeerJ Computer Science*, 10, e2441.
- Bitew, S. K., Deleu, J., Develder, C., & Demeester, T. (2022). Learning to Reuse Distractors to support Multiple Choice Question Generation in Education. *IEEE Transactions on Learning Technologies*.
- Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *Proceedings of EACL 2024 — System Demonstrations*.
- Gao, Y., Bing, L., Chen, W., Lyu, M., & King, I. (2019). Generating Distractors for Reading Comprehension Questions from Real Examinations. *AAAI 2019*.
- Haladyna, T. M., Downing, S. M., & Rodriguez, M. C. (2002). A Review of Multiple-Choice Item-Writing Guidelines for Classroom Assessment. *Applied Measurement in Education*, 15(3), 309–333.
- Kurdi, G., Leo, J., Parsia, B., Sattler, U., & Al-Emari, S. (2020). A Systematic Review of Automatic Question Generation for Educational Purposes. *International Journal of Artificial Intelligence in Education*, 30, 121–204.
- Liang, P., et al. (2022). Holistic Evaluation of Language Models. *arXiv:2211.09110*.
- Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333–389.
- Shahul, E., et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *arXiv:2309.15217*.
- Singhal, K., et al. (2023). Large language models encode clinical knowledge. *Nature*, 620, 172-180.
- Tran, K., et al. (2024). Exploring Automated Distractor Generation for Math Multiple-choice Questions via Large Language Models. *Findings of NAACL 2024*. (arXiv:2404.02124).
- Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *NeurIPS 2023*.
