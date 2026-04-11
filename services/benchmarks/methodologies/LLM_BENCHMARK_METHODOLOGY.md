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

Four models produce a benchmark matrix of 4 generators × 12 RAG configurations × 10 golden questions = **480 evaluation rows**. This is substantial enough for thesis analysis while remaining computationally tractable with local inference. Adding more models would increase runtime linearly without proportional analytical value — the four selected models already cover three model families (Mistral, Meta, Google, Microsoft) and two size classes (3.8B vs 7–9B).

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
3. **Cost efficiency** — Gemini 2.5 Flash Lite is the cheapest tier of the Gemini 2.5 family and completed the 480-row evaluation for well under $1 on the paid tier, keeping the evaluation accessible for academic research. The free tier's daily cap (20 requests/day for Flash Lite) is not sufficient for a 480-row run, so a billing-enabled project is required.

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

1. **Stem clarity** — is the question stem well-formed, unambiguous, and self-contained? A stem scoring 5 is clear and focused; a stem scoring 1 is grammatically broken, ambiguous, or requires the options to be understood.
2. **Distractor plausibility** — are the three incorrect options plausible-but-wrong: topically relevant, not trivially identifiable as wrong, and meaningfully distinct from the correct answer? A score of 5 means all three distractors are genuine competitors a learner could reasonably consider; a score of 1 means the distractors are absurd, off-topic, near-duplicates of the correct answer, or obviously nonsensical.
3. **Pedagogical appropriateness** — does the question probe meaningful understanding of the context rather than superficial recall of a specific phrase? A score of 5 tests conceptual understanding or application; a score of 1 is trivial fact lookup or off-topic.

The three sub-scores are averaged and normalised to a 0–1 scale to produce `mcq_quality`:

```
mcq_quality = mean(stem_clarity, distractor_plausibility, pedagogical_appropriateness) / 5
```

The rubric prompt passes the retrieved context, the parsed stem, the four options, the declared correct letter, and the explanation to the judge, which is instructed to return strict JSON with the three scores. The rubric logic is implemented in `services/benchmarks/scoring/rubric.py` and is shared by both the production scoring path (`llm_benchmark.py`, `llm_ragas_score.py`) and the offline rescoring tool (`benchmarks/investigations/rescore_mcq_rubric.py`).

**Why a rubric replaces RAGAS `answer_relevancy`.** The original benchmark composite included RAGAS `answer_relevancy`, which reverse-engineers candidate questions from the "answer" text and measures their mean cosine similarity to the golden question via an embedding model. On the first benchmark run this metric clustered every generator at 0.35–0.38, with an absolute spread of 0.029 across the four models — insufficient to separate them. An offline investigation (Finding 4) ruled out payload shape as the cause: rescoring with a `why`-only payload under production MiniLM embeddings moved the metric by at most ±0.03 per generator. The clustering is a real consequence of three compounding factors:

1. **Surface-form compression under deterministic decoding and a strict JSON schema.** With `temperature=0`, a fixed seed, identical context, and a schema that constrains every generator to `{stem, 4 options, correct letter, why}`, the degrees of freedom for the "answer" text shrink dramatically. Sentence-embedding metrics cannot discriminate outputs that differ only in lexical choice — a format-bias / ceiling effect discussed in the HELM framework (Liang et al., 2022) and corroborated by MT-Bench's observation that closed-form tasks compress judge scores (Zheng et al., 2023).
2. **`answer_relevancy` is designed for open-ended QA.** The metric reverse-engineers candidate questions from the answer text and measures similarity to the original question (Es et al., 2024). When the answer already contains a question stem (as in MCQ generation), the reverse-engineering step is partly tautological.
3. **Statistical compression at small sample sizes.** With 120 evaluation rows per generator, per-question variance of the metric dominates the between-model signal. The metric does discriminate *within* a model (per-row scores range from 0.01 to 0.73) but these cancel on the model mean.

The rubric-based `mcq_quality` metric avoids all three issues by evaluating the full MCQ structure against explicit quality dimensions rather than measuring similarity against a reference.

**Why this rubric and these three dimensions.** The three-dimension rubric is adapted from the Med-PaLM clinical QA evaluation protocol (Singhal et al., 2023), which established LLM-as-judge rubric scoring as a valid alternative to aggregate similarity metrics in high-stakes educational/clinical QA. The specific dimensions (stem clarity, distractor plausibility, pedagogical appropriateness) correspond to the MCQ quality criteria identified by Kurdi et al. (2020) in their systematic review of automatic question generation for educational purposes, where similarity-to-reference is categorised as the weakest family of MCQ evaluation methods. Distractor plausibility in particular is known from the MCQ generation literature (Gao et al., 2019; Bitew et al., 2022) to be the dimension on which generator models differ most meaningfully, which is borne out by the empirical results in the LLM Benchmark Report Finding 5.

**Why it matters for the pipeline:** A model can be faithful to the context (no hallucination) and topically on-point but still produce a question with absurd distractors, an ambiguous stem, or a trivial-recall framing — all of which degrade the pedagogical value of the question for teacher training. The rubric surfaces these failure modes directly. Empirically it also discriminates: on the 425 rescorable rows, `mcq_quality` ranges from 0.697 (mistral-7b) to 0.806 (phi3.5-3.8b), with distractor plausibility showing the largest between-model gap (3.01–3.68 on the 1–5 scale; see LLM Benchmark Report Finding 5).

### 4.4.1 Deprecated: RAGAS answer relevancy (retained for schema compatibility)

Prior benchmark runs (before the Finding 5 rebalance) included RAGAS `answer_relevancy` at 10 % of the composite score. The metric is documented here for reproducibility: it was computed with the Gemini 2.5 Flash Lite judge and `sentence-transformers/all-MiniLM-L6-v2` as the embedding model (the same production embedding used by `llm_ragas_score.py` and the one empirically validated as best-on-corpus in the RAG Retrieval Benchmark Report). New benchmark runs no longer compute this metric, but the `answer_relevancy` column is retained in the output CSV schema so that pre-Finding-5 evaluation CSVs remain readable. The code path in `llm_benchmark.py` and `llm_ragas_score.py` is commented out rather than deleted so it can be re-enabled for ad-hoc investigations. See LLM Benchmark Report, Finding 4 for the full analysis of why this metric was deprecated.

### 4.5 Context relevancy

**What:** Were the retrieved chunks relevant to the question?

**How:** Carried over from the RAG benchmark CSV (`context_relevancy` column). This is the RAGAS `context_precision` score from Phase 6, not re-evaluated here.

**Why it is included:** The composite score needs to account for retrieval quality because a model cannot generate a good question from irrelevant chunks. Including context relevancy means the composite score reflects end-to-end pipeline quality, not just generation quality in isolation.

### 4.6 Composite score (Weighted Sum Model)

**Formula (v2, post-Finding-5):** `(faithfulness × 0.4) + (context_relevancy × 0.3) + (mcq_quality × 0.2) + (format_compliance × 0.1)`

**Prior formula (v1, deprecated):** `(faithfulness × 0.4) + (context_relevancy × 0.4) + (answer_relevancy × 0.1) + (format_compliance × 0.1)`

**Theoretical Framework & Weight Rationale:**

The composite score uses a Domain-Specific Weighted Sum Model (WSM), a standard technique in Multi-Criteria Decision Analysis (MCDA). As argued by the Holistic Evaluation of Language Models (HELM) framework (Liang et al., 2022), LLM evaluation cannot rely on universal metrics; it must be use-case specific. For a high-stakes domain like student mental health, safety and factual grounding must disproportionately dominate the evaluation criteria (similar to clinical AI benchmarks like Singhal et al., 2023).

- **70 % on factual grounding (faithfulness 0.4 + context relevancy 0.3):** For psychological educational content, the primary risk is clinical misinformation. The high weighting ensures severe penalties for hallucinated claims. A well-formatted, pedagogically sound question that teaches factually incorrect anxiety interventions is a catastrophic failure mode, whereas poor formatting is merely an engineering inconvenience.
- **20 % on MCQ quality (`mcq_quality`):** The rubric-based metric replaces `answer_relevancy` and takes a larger weight because it is a structurally validated signal on MCQ-specific dimensions (stem clarity, distractor plausibility, pedagogical appropriateness), not a surface-similarity proxy. Pedagogically, distractor quality directly determines whether an MCQ tests genuine understanding; a question with absurd distractors is trivially answerable and therefore pedagogically worthless regardless of its factual grounding.
- **10 % on format compliance:** A hard production requirement. JSON breakage can often be mitigated downstream via output parsers or retry loops, making it an engineering metric rather than a core clinical safety metric; however, it is retained in the composite because it meaningfully discriminates generators (range 0.742–1.000 across the four models) and a production-facing composite must reflect deployment-usability as well as pedagogical quality.

**Why the 0.3 weight on context relevancy (down from 0.4 in v1).** In the decoupled pipeline architecture (§5), every generator is evaluated against identical retrieval contexts frozen in the RAG benchmark CSV. Consequently `context_relevancy` is a constant across the four generators for any given RAG configuration — in the 425 rescored rows the value is identical at 0.795 for every generator. Its 0.4 weight in v1 contributed no discriminative signal between generators; it only served as a constant floor. Reducing the weight to 0.3 frees 0.1 composite-score-mass to be allocated to `mcq_quality`, which does discriminate. The 70 % factual-grounding total (down from 80 %) remains consistent with the HELM + Med-PaLM precedent for high-stakes educational AI, because the MCQ quality rubric itself includes structural-quality dimensions that are pedagogically load-bearing for clinical-educational content.
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
- **Generation is the expensive step** (~8 hours on local hardware for 480 rows). It runs once and its outputs are preserved in the CSV.
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

The benchmark uses the same MCQ prompt template as the production system (`services/llm/prompts.py`) to ensure evaluation reflects real-world performance. The prompt instructs the model to:

1. Generate exactly one multiple-choice question from the provided excerpt
2. Base the question only on the excerpt (no external knowledge)
3. Produce exactly 4 options labelled A–D with one correct answer
4. Include a short explanation (`why`) grounded in the excerpt
5. Return the output as strict JSON

All generation uses `temperature=0` and a fixed seed (`seed=7`) for deterministic output.

---

## 7. Output Format

Results are written to `results/llm_YYYYMMDD_HHMMSS.csv` — one row per question per generator model per RAG configuration (480 rows for 4 models × 120 RAG rows). `llm_benchmark.py` writes the generation columns (`raw_output`, `generated_answer`, `format_compliance`, `response_time_s`) and saves incrementally after each model. `llm_ragas_score.py` then updates the same file in place with `faithfulness`, the four rubric columns (`stem_clarity`, `distractor_plausibility`, `pedagogical_appropriateness`, `mcq_quality`), and `composite_score`, resumable at the batch level if interrupted.

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
| `context_relevancy` | float/null | RAGAS context precision (from RAG CSV) |
| `composite_score` | float/null | Weighted composite v2 (§4.6): `0.4·faith + 0.3·ctx + 0.2·mcq_quality + 0.1·fmt` |

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

- Bitew, S. K., Deleu, J., Develder, C., & Demeester, T. (2022). Learning to Reuse Distractors to support Multiple Choice Question Generation in Education. *IEEE Transactions on Learning Technologies*.
- Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *Proceedings of EACL 2024 — System Demonstrations*.
- Gao, Y., Bing, L., Chen, W., Lyu, M., & King, I. (2019). Generating Distractors for Reading Comprehension Questions from Real Examinations. *AAAI 2019*.
- Kurdi, G., Leo, J., Parsia, B., Sattler, U., & Al-Emari, S. (2020). A Systematic Review of Automatic Question Generation for Educational Purposes. *International Journal of Artificial Intelligence in Education*, 30, 121–204.
- Liang, P., et al. (2022). Holistic Evaluation of Language Models. *arXiv:2211.09110*.
- Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333–389.
- Shahul, E., et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *arXiv:2309.15217*.
- Singhal, K., et al. (2023). Large language models encode clinical knowledge. *Nature*, 620, 172-180.
- Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *NeurIPS 2023*.
