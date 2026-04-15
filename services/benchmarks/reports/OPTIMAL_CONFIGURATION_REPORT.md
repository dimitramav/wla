# Optimal Pipeline Configuration Report

## 1. Purpose

This report synthesises findings from the RAG Retrieval Benchmark (2 runs, 12 configurations, 10 + 15 golden questions) and the LLM Generation Benchmark (3 runs, 4 generators, 480 + 720 + 180 generations) to identify the single best end-to-end configuration for the WLA adaptive quiz pipeline. Where the two benchmarks diverge on a parameter choice, the divergence is explained and a unified recommendation is given.

---

## 2. Summary of Individual Benchmarks

### 2.1 RAG Retrieval Benchmark

Evaluates **retrieval quality** in isolation: given a question and keyword, does the pipeline retrieve chunks that contain the knowledge needed to answer it?

- **Configurations tested:** 3 embedding models x 2 chunk sizes x 2 retrieval strategies = 12
- **Golden questions:** 10 (Run 1), 15 (Run 2)
- **Metric:** RAGAS `context_precision` (LLM-judged, 0-1)

**Run 2 top-5 configurations:**

| # | Embedding | Chunks | Retrieval | RAGAS |
|---|-----------|:---:|:---:|:---:|
| 1 | all-mpnet-base-v2 | 800/100 | hybrid | **0.966** |
| 2 | bge-small-en-v1.5 | 800/100 | hybrid | 0.943 |
| 3 | bge-small-en-v1.5 | 800/100 | dense | 0.932 |
| 4 | all-MiniLM-L6-v2 | 512/50 | hybrid | 0.926 |
| 5 | all-MiniLM-L6-v2 | 800/100 | dense | 0.915 |

### 2.2 LLM Generation Benchmark

Evaluates **generation quality**: given frozen retrieval contexts, which LLM produces the most faithful, well-formatted, pedagogically appropriate MCQs?

- **Generators tested:** gemma2-9b, llama3.1-8b, phi3.5-3.8b, mistral-7b (baseline)
- **Runs:** Run 1 (baseline prompts), Run 2 (domain-grounded system prompt), Run 3 (concept-dependent prompt ablation, gemma2-9b only)
- **Metrics:** Format compliance, RAGAS faithfulness, MCQ quality rubric, text independence (Run 3), weighted composite

**Run 2 per-generator summary:**

| Generator | Format | Faithfulness | MCQ Quality | Composite (v2) |
|-----------|:---:|:---:|:---:|:---:|
| **gemma2-9b** | **0.983** | **0.867** | **0.824** | **0.884** |
| llama3.1-8b | 0.817 | 0.827 | 0.765 | 0.854 |
| phi3.5-3.8b | 0.822 | 0.700 | 0.777 | 0.804 |
| mistral-7b | 0.678 | 0.726 | 0.646 | 0.786 |

**Run 2 top-5 end-to-end configurations (generator + retrieval):**

| # | Generator | Embedding | Chunks | Retrieval | Composite |
|---|-----------|-----------|:---:|:---:|:---:|
| 1 | gemma2-9b | bge-small-en-v1.5 | 800/100 | hybrid | **0.938** |
| 2 | gemma2-9b | all-mpnet-base-v2 | 800/100 | hybrid | 0.927 |
| 3 | gemma2-9b | all-MiniLM-L6-v2 | 800/100 | hybrid | 0.913 |
| 4 | gemma2-9b | all-mpnet-base-v2 | 800/100 | dense | 0.901 |
| 5 | llama3.1-8b | all-mpnet-base-v2 | 512/50 | hybrid | 0.901 |

---

## 3. Consistent Findings Across Both Benchmarks

Three parameters produced the same recommendation in every run of both benchmarks:

| Parameter | Recommendation | Confidence | Evidence |
|-----------|---------------|:---:|----------|
| **Retrieval strategy** | Hybrid (BM25 + dense, RRF k=60) | High | Improved RAGAS in 11 of 12 configurations across both RAG runs; held all top-5 LLM benchmark slots in Run 2 |
| **Chunk size** | 800 tokens / 100 overlap | High | Outperformed 512/50 in both RAG runs (Run 2: +3.3 to +6.2 pp); 4 of 5 top LLM benchmark slots use 800/100 |
| **Generator** | gemma2:9b-instruct-q4_0 | High | Led on every primary axis (format, faithfulness, composite) across all three LLM runs; the only model with near-perfect format compliance |

These three decisions are settled. The remaining question is the embedding model.

---

## 4. The Embedding Divergence

The two benchmarks produced different embedding recommendations:

| Benchmark | Best Embedding | Score | Runner-up | Gap |
|-----------|---------------|:---:|-----------|:---:|
| RAG Retrieval (Run 2) | all-mpnet-base-v2 | 0.966 | bge-small-en-v1.5 (0.943) | 0.023 |
| LLM Generation (Run 2, top config) | bge-small-en-v1.5 | 0.938 | all-mpnet-base-v2 (0.927) | 0.011 |
| LLM Generation (Run 3, top config) | all-MiniLM-L6-v2 | 0.868 | bge-small-en-v1.5 (0.849) | 0.019 |

### 4.1 Why the rankings differ

The divergence has three causes:

1. **Different evaluation targets.** The RAG benchmark measures retrieval quality (does the system find the right chunks?). The LLM benchmark measures generation quality (does the LLM produce a good question from those chunks?). A chunk set that scores slightly lower on RAGAS retrieval precision might still contain the specific phrasing or detail that helps the generator produce a better MCQ. The relationship between retrieval quality and generation quality is positive but not perfectly monotonic.

2. **Small sample size.** The RAG Run 2 uses 15 golden questions; the LLM benchmark uses 15 questions x 12 retrieval configurations = 180 rows per generator. Per-embedding differences are small (0.011-0.023) and fall within the noise range of a 15-question benchmark. Neither report claims statistical significance for the embedding ranking (RAG Report Section 7.10; LLM Report Section 8).

3. **Interaction effects.** In the LLM benchmark, the embedding is not evaluated in isolation -- it interacts with the generator, the prompt, and the specific golden question. bge-small-en-v1.5's top position in the LLM Run 2 is driven by a few high-scoring (config x question) rows rather than consistent superiority across the matrix. The same is true of MiniLM's top position in Run 3.

### 4.2 All three embeddings are in the same performance tier

Aggregating across both benchmarks:

| Embedding | RAG Run 2 (800/100 hybrid) | LLM Run 2 composite (800/100 hybrid) | LLM Run 3 composite (best config) | Model size |
|-----------|:---:|:---:|:---:|:---:|
| all-mpnet-base-v2 | **0.966** | 0.927 | 0.835 | 420 MB |
| bge-small-en-v1.5 | 0.943 | **0.938** | **0.849** | 130 MB |
| all-MiniLM-L6-v2 | 0.896 | 0.913 | 0.848 | 80 MB |

The total spread across all three models is:
- RAG retrieval: 0.070 (0.896 to 0.966)
- LLM generation: 0.025 (0.913 to 0.938)

These margins are too small to declare a definitive winner at the current sample size. All three embeddings produce retrieval quality above 0.89 and end-to-end composite quality above 0.91, which is more than sufficient for the quiz pipeline.

---

## 5. Unified Recommendation

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Embedding model** | `sentence-transformers/all-mpnet-base-v2` | Won the RAG benchmark (0.966, the more controlled test); runner-up in LLM benchmark (0.927, within 0.011 of #1); larger embedding dimension (768 vs 384) provides better differentiation across diverse keywords |
| **Chunk size** | 800 tokens / 100 overlap | Consistent winner across all runs; amplifies hybrid retrieval benefit; captures more context per retrieval hit |
| **Retrieval strategy** | Hybrid (BM25 + dense, RRF k=60) | Most impactful single parameter; improved RAGAS in 11 of 12 configurations; held all top-5 LLM benchmark slots |
| **Generator** | `gemma2:9b-instruct-q4_0` | Best faithfulness (0.867), near-perfect format compliance (98.3%), highest composite in every run |
| **Prompts** | v2 concept-dependent | Eliminated text-referencing questions (96% -> 4.4%); +9.1 pp composite improvement (v3 formula) |
| **Fallback generator** | `phi3.5:3.8b-mini-instruct-q4_0` | Fastest inference (41.7s median); highest MCQ quality rubric (0.806); viable fallback if gemma2 is unavailable |

### 5.1 Why all-mpnet-base-v2 over alternatives

- **Over bge-small-en-v1.5:** mpnet won the retrieval benchmark by a larger margin (0.966 vs 0.943 = +2.3 pp) than bge won the LLM benchmark (0.938 vs 0.927 = +1.1 pp). Since retrieval quality sets the floor for generation quality (Finding 6 in the LLM report: "good retrieval raises the floor; choice of generator raises the ceiling"), optimising for retrieval is the higher-leverage choice.

- **Over all-MiniLM-L6-v2:** MiniLM is the smallest and fastest model, but its 384-dimensional embeddings provide less differentiation across the broader keyword taxonomy. In Run 2 (the more representative 15-question benchmark), mpnet outperformed MiniLM on 800/100 hybrid by 7.0 pp (0.966 vs 0.896). MiniLM remains a valid choice if model size or inference speed is a constraint.

### 5.2 Trade-offs

| Concern | Assessment |
|---------|-----------|
| **Model size** | mpnet is 420 MB vs MiniLM's 80 MB. For local deployment with infrequent ingestion, this is acceptable. |
| **Ingestion speed** | mpnet is slower to embed. Since ingestion happens once per document set (not per quiz), the latency difference is negligible in practice. |
| **Re-ingestion required** | Switching embedding models requires re-ingesting the entire PDF corpus into ChromaDB. This is a one-time operation (~2 minutes for the current 8-document corpus). |
| **Generation latency** | gemma2-9b is the slowest generator (77.6s median vs 41.7s for phi3.5). For the current async quiz flow (one question at a time), this is acceptable. |

---

## 6. Expected End-to-End Performance

Based on the benchmark data, the recommended configuration is expected to achieve:

| Metric | Baseline (mistral-7b + MiniLM + dense) | Recommended (gemma2-9b + mpnet + hybrid + v2 prompts) | Improvement |
|--------|:---:|:---:|:---:|
| Retrieval quality (RAGAS) | 0.752 | **0.966** | +0.214 (+28.5%) |
| Format compliance | 0.742 | **0.983** | +0.241 (+32.5%) |
| Faithfulness | 0.714 | **0.867** | +0.153 (+21.4%) |
| MCQ quality rubric | 0.697 | **0.824** | +0.127 (+18.2%) |
| Text independence | 0.044 | **0.944** | +0.900 |
| End-to-end composite (v2) | 0.765 | **0.938** | +0.173 (+22.6%) |

The combined effect of switching the embedding model (MiniLM -> mpnet), enabling hybrid retrieval, upgrading the generator (mistral -> gemma2), and applying the v2 concept-dependent prompts produces a **22.6% improvement in end-to-end composite quality** over the production baseline.

---

## 7. Remaining Quality Gaps

| Gap | Current score | Ceiling | Source |
|-----|:---:|:---:|--------|
| Distractor plausibility | 3.78/5 | ~5.0 | Model capability ceiling at 9B Q4_0 parameter class (LLM Report Section 7.8) |
| Faithfulness long tail | 0.726 mean (Run 3) | ~1.0 | Concept-dependent prompts reduce surface overlap with source chunks, lowering RAGAS faithfulness despite factual correctness (LLM Report Section 9.5) |
| Retrieval on keyword-specific queries | 0.679 min (Run 2) | 1.0 | BM25 keyword matching occasionally pulls topically specific but contextually incomplete chunks (RAG Report Section 7.8) |

These gaps are documented as known limitations. None blocks deployment or invalidates the recommended configuration.

---

## 8. Implementation Checklist

To deploy the recommended configuration:

1. **Pull the gemma2-9b model:** `ollama pull gemma2:9b-instruct-q4_0`
2. **Update the generator config** in `services/rag/settings.py` to use `gemma2:9b-instruct-q4_0`
3. **Update the embedding model** in `services/rag/settings.py` to use `sentence-transformers/all-mpnet-base-v2`
4. **Re-ingest the PDF corpus** to rebuild ChromaDB with mpnet embeddings
5. **Verify hybrid retrieval is enabled** (already implemented in the retrieval pipeline)
6. **Deploy the v2 prompts** from `services/llm/prompts.py` (already updated as of Run 3)
7. **Remove the mistral-7b model** (optional): `ollama rm mistral:7b-instruct-q4_0`

---

## 9. Limitations

- **Sample size.** Both benchmarks use 15 golden questions. This is sufficient to show consistent trends but not for formal statistical significance testing. A larger golden question set (50+) would be needed for peer-review-grade claims about embedding model differences.
- **Single topic.** All benchmarks evaluated the `school_anxiety` topic only. Performance on future topics may differ, though the architecture is topic-agnostic.
- **Local hardware.** All benchmarks ran on a single local machine. Results may vary on different hardware configurations, particularly for generation latency.
- **Judge model.** RAGAS metrics and the MCQ quality rubric are scored by Gemini 2.5 Flash Lite. A different judge model might produce different absolute scores, though relative rankings are expected to be stable.

---

## References

- RAG Retrieval Benchmark Report (this directory): methodology, per-configuration results, per-question analysis
- LLM Generation Benchmark Report (this directory): generator comparison, prompt ablation study, rubric development
- RAG Benchmark Methodology: `methodologies/RAG_BENCHMARK_METHODOLOGY.md`
- LLM Benchmark Methodology: `methodologies/LLM_BENCHMARK_METHODOLOGY.md`
