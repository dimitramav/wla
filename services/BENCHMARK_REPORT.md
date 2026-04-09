# RAG Retrieval Benchmark Report

## 1. Experimental Setup

### Objective

Evaluate the retrieval quality of the WLA RAG pipeline across different configurations to determine which combination of embedding model, chunk size, and retrieval strategy produces the most relevant context for quiz question generation about student mental health.

### What is being evaluated

This benchmark tests **retrieval quality** — whether the system retrieves text chunks that contain the knowledge needed to generate a correct quiz question. It does not evaluate the LLM's question generation quality, which is a separate concern.

### Configurations tested

| Parameter | Values |
|-----------|--------|
| Embedding models | `all-MiniLM-L6-v2` (baseline), `all-mpnet-base-v2`, `bge-small-en-v1.5` |
| Chunk sizes | 512 tokens / 50 overlap, 800 tokens / 100 overlap (baseline) |
| Retrieval strategies | Dense (cosine similarity), Hybrid (BM25 + dense via Reciprocal Rank Fusion) |

This produces **12 configurations**, each evaluated against **10 manually curated, corpus-grounded golden questions**, for a total of **120 evaluation rows**.

### Golden questions

The golden question set consists of 10 questions curated by the researcher from the ingested PDF corpus. Initial drafts were generated with AI assistance; each question and its ground-truth answer were then individually verified by the researcher against the cited source passage to ensure factual accuracy and source traceability. Questions span both document types in the corpus — practitioner guides (Anna Freud National Centre) and peer-reviewed research papers (Schlesier et al. 2023, Johnson et al. 2023) — to ensure retrieval quality is evaluated across the heterogeneous writing styles present in the corpus (see "Why retrieval configuration is non-trivial" in `methodology_hybrid_search.md`). Each question is tagged with taxonomy keywords from the platform's difficulty hierarchy. This ensures the benchmark measures whether the system retrieves the *specific chunks that contain the answer*, not whether it retrieves generically related content.

### Metrics

- **Cosine similarity (top_score):** How semantically similar the top retrieved chunk is to the query. High values (close to 1.0) mean the chunk "sounds like" the question. This is the retrieval system's native scoring mechanism.
- **RAGAS context_precision:** An LLM-judged metric that assesses whether the retrieved chunks contain the knowledge needed to answer the question. Scored 0–1, where 1.0 means the retrieved context fully supports the ground-truth answer. This metric is evaluated using Mistral 7B (the same LLM used in the production pipeline) via the RAGAS framework (Shahul et al., 2023).

The distinction between these two metrics is critical: a chunk can be semantically similar to a question (high cosine score) without actually containing the answer (low RAGAS score). This gap is exactly what the benchmark is designed to surface.

---

## 2. Results

### 2.1 Summary by configuration

| Model | Chunks | Retrieval | Avg Cosine Score | Avg RAGAS |
|-------|--------|-----------|:---:|:---:|
| all-MiniLM-L6-v2 | 512/50 | dense | 0.964 | 0.746 |
| all-MiniLM-L6-v2 | 512/50 | hybrid | 0.858 | 0.783 |
| all-MiniLM-L6-v2 | 800/100 | dense | 1.000 | 0.752 |
| **all-MiniLM-L6-v2** | **800/100** | **hybrid** | **0.924** | **0.867** |
| all-mpnet-base-v2 | 512/50 | dense | 0.973 | 0.740 |
| all-mpnet-base-v2 | 512/50 | hybrid | 0.910 | 0.819 |
| all-mpnet-base-v2 | 800/100 | dense | 1.000 | 0.752 |
| all-mpnet-base-v2 | 800/100 | hybrid | 0.890 | 0.855 |
| bge-small-en-v1.5 | 512/50 | dense | 0.978 | 0.772 |
| bge-small-en-v1.5 | 512/50 | hybrid | 0.925 | 0.848 |
| bge-small-en-v1.5 | 800/100 | dense | 1.000 | 0.770 |
| bge-small-en-v1.5 | 800/100 | hybrid | 0.927 | 0.834 |

**Best configuration: all-MiniLM-L6-v2, 800/100 chunks, hybrid retrieval (RAGAS = 0.867)**

### 2.2 Effect of retrieval strategy (dense vs hybrid)

| Model | Chunks | Dense RAGAS | Hybrid RAGAS | Delta |
|-------|--------|:---:|:---:|:---:|
| all-MiniLM-L6-v2 | 512/50 | 0.746 | 0.783 | **+0.037** |
| all-MiniLM-L6-v2 | 800/100 | 0.752 | 0.867 | **+0.115** |
| all-mpnet-base-v2 | 512/50 | 0.740 | 0.819 | **+0.079** |
| all-mpnet-base-v2 | 800/100 | 0.752 | 0.855 | **+0.104** |
| bge-small-en-v1.5 | 512/50 | 0.772 | 0.848 | **+0.076** |
| bge-small-en-v1.5 | 800/100 | 0.770 | 0.834 | **+0.064** |

Hybrid retrieval improves RAGAS context_precision by **+3.7 to +11.5 percentage points** across all configurations. The improvement is consistent and positive in every case, with the largest gains observed at 800/100 chunk size.

### 2.3 Effect of chunk size

| Model | Dense 512/50 | Dense 800/100 | Delta |
|-------|:---:|:---:|:---:|
| all-MiniLM-L6-v2 | 0.746 | 0.752 | +0.006 |
| all-mpnet-base-v2 | 0.740 | 0.752 | +0.012 |
| bge-small-en-v1.5 | 0.772 | 0.770 | -0.002 |

Chunk size has **minimal effect on RAGAS scores** in dense retrieval (< 1.2% difference). However, larger chunks amplify the benefit of hybrid retrieval — the biggest hybrid improvements occur with 800/100 chunks. This suggests that larger chunks provide more keyword surface area for BM25 matching, making the hybrid combination more effective.

### 2.4 Effect of embedding model

| Retrieval | MiniLM | mpnet | bge-small | Spread |
|-----------|:---:|:---:|:---:|:---:|
| Dense, 800/100 | 0.752 | 0.752 | 0.770 | 0.018 |
| Hybrid, 800/100 | 0.867 | 0.855 | 0.834 | 0.033 |
| Dense, 512/50 | 0.746 | 0.740 | 0.772 | 0.032 |
| Hybrid, 512/50 | 0.783 | 0.819 | 0.848 | 0.065 |

The spread between embedding models is **1.8–6.5 percentage points** — modest compared to the retrieval strategy effect. No single model dominates across all configurations. For 800/100 hybrid (the best-performing setting), all-MiniLM-L6-v2 slightly outperforms the others despite being the smallest model.

### 2.5 Per-question analysis (best configuration vs baseline)

Comparing the production baseline (all-MiniLM-L6-v2, 800/100, dense) against the best configuration (same model and chunks, hybrid):

| Question (abbreviated) | Dense RAGAS | Hybrid RAGAS | Change |
|------------------------|:---:|:---:|:---:|
| Teacher reassuring a worried student | 0.333 | 1.000 | **+0.667** |
| Challenging an anxious thought | 0.478 | 1.000 | **+0.522** |
| Trends in persistent school absence | 0.200 | 0.500 | **+0.300** |
| Teacher recognition of anxiety vs ADHD | 0.700 | 0.367 | -0.333 |
| Early physical and behavioural signs | 0.806 | 0.804 | 0.000 |
| Calm teacher importance | 1.000 | 1.000 | 0.000 |
| Anxiety Thermometer | 1.000 | 1.000 | 0.000 |
| Graded exposure approach | 1.000 | 1.000 | 0.000 |
| Whole-school approach | 1.000 | 1.000 | 0.000 |
| Bullying–anxiety–absenteeism link | 1.000 | 1.000 | 0.000 |

Hybrid retrieval dramatically improves the three weakest questions (the ones where dense retrieval found semantically similar but non-answer-bearing chunks). However, one question ("teacher recognition of anxiety vs ADHD") regresses from 0.700 to 0.367. This suggests that for research-oriented questions with specialised terminology, BM25 keyword matching may pull in more specific but less complete chunks.

---

## 3. Key Findings

### Finding 1: Retrieval strategy matters more than model choice

The single most impactful change is switching from dense to hybrid retrieval. Across all 6 model×chunk combinations, hybrid consistently improves RAGAS scores. The improvement (+3.7 to +11.5 pp) is larger than the variation between any two embedding models (< 6.5 pp). This means that for this domain corpus, **how you combine retrieval signals matters more than which embedding model you use**.

### Finding 2: Hybrid retrieval rescues failing queries

Three questions that scored below 0.5 with dense retrieval improved to 0.5–1.0 with hybrid. These are questions where the answer exists in a specific passage that uses different vocabulary than the question itself. BM25's exact keyword matching complements the embedding model's semantic matching, finding chunks that cosine similarity alone misses.

### Finding 3: The cosine similarity ceiling is misleading

Dense retrieval with 800/100 chunks achieves perfect 1.0 cosine similarity across all models — yet RAGAS scores average only 0.752. This demonstrates that high semantic similarity does not guarantee answer-relevant retrieval. A chunk about "school anxiety" will score high cosine similarity to any question about school anxiety, even if it discusses a different sub-topic. RAGAS catches this distinction.

### Finding 4: Hybrid retrieval is not universally better per question

One question regresses with hybrid (-0.333). This indicates a known trade-off: BM25 can over-weight keyword matches that are topically specific but contextually incomplete. In the aggregate, the gains substantially outweigh this regression, but it is worth noting that hybrid is not a guaranteed improvement for every individual query.

### Finding 5: Chunk size interacts with retrieval strategy

Chunk size alone has negligible effect (< 1.2 pp). But it amplifies hybrid retrieval: the largest hybrid improvement (+11.5 pp) occurs at 800/100, while at 512/50 the improvement is only +3.7 pp for the same model. Larger chunks provide more keyword surface for BM25 while also carrying more contextual information per retrieval hit.

---

## 4. Recommended Configuration

Based on the benchmark results, the recommended production configuration is:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | Best RAGAS score at 800/100 hybrid; fastest inference; smallest memory footprint; already the production default |
| Chunk size | 800 tokens, 100 overlap | Amplifies hybrid benefit; negligible dense-only difference; already the production default |
| Retrieval strategy | **Hybrid (BM25 + dense, RRF k=60)** | +11.5 pp RAGAS improvement over dense baseline |

This configuration achieves an average RAGAS context_precision of **0.867**, up from 0.752 with the current dense-only baseline — a **15.3% relative improvement** in retrieval relevance.

Notably, this recommendation requires no model changes and no re-ingestion. The only change is enabling hybrid retrieval at query time, which adds BM25 scoring over the existing chunk pool.

---

## 5. Should Further Optimisation Be Pursued?

### What the current score means

A RAGAS context_precision of 0.867 means that on average, 87% of the retrieved context is relevant to answering the question. For an educational quiz platform, this is a strong result — the LLM receives mostly relevant material to generate questions from.

### Where the remaining gap is

The 13% gap comes from two sources:
1. **Two questions score below 0.5** — the research-oriented questions about absence statistics and teacher recognition of anxiety. These reference specific numerical findings from academic papers, which are harder to retrieve with general-purpose embeddings.
2. **Chunk boundaries** — some answers span multiple paragraphs that get split across chunks, diluting relevance scores.

### What could improve scores further

| Approach | Expected gain | Effort | Recommendation |
|----------|:---:|:---:|:---:|
| Fine-tuning embeddings on mental health vocabulary | Moderate (~5 pp) | High | Not recommended for v1 |
| Domain-specific embedding model (PubMedBERT, etc.) | Unknown | Medium | Could explore in v2 |
| Semantic chunking (split by paragraph/section, not token count) | Moderate (~3-5 pp) | Medium | Worth investigating |
| Query expansion (adding synonyms to search queries) | Low (~2-3 pp) | Low | Easy to try |
| Increasing top-k from 5 to 8 retrieved chunks | Low (~1-2 pp) | Trivial | Easy to try |
| Adding more source PDFs to the corpus | Variable | Low | Recommended — more coverage = better answers |

### Verdict

The current 0.867 score is strong enough for the v1 milestone. The hybrid retrieval improvement is the biggest single gain available without significant engineering effort. Further optimisation would yield diminishing returns relative to the work involved. For the thesis, the key narrative is: **a simple hybrid retrieval strategy improved context relevance by 15% over dense-only retrieval, with no model retraining, no additional infrastructure, and no changes to the existing embedding pipeline.**

---

## 6. Methodology Notes

- **Evaluation LLM:** Mistral 7B Instruct (Q4_0 quantisation), same model used in the production pipeline. Using the same model for both generation and evaluation creates a potential self-assessment bias, but ensures the evaluation reflects the actual system's capabilities.
- **RAGAS version:** 0.1.22 with `context_precision` metric. Evaluation ran sequentially (`max_workers=1`) against a local Ollama instance.
- **Hybrid retrieval implementation:** BM25 (Robertson & Zaragoza, 2009) via `rank_bm25` library, combined with dense cosine similarity through Reciprocal Rank Fusion (Cormack et al., SIGIR 2009) with k=60. RRF determines chunk ordering; cosine similarity remains the quality score.
- **Statistical limitations:** 10 golden questions is a small sample. Results indicate consistent trends but are not sufficient for statistical significance testing. A larger question set (50+) would be needed for robust significance claims.
- **Reproducibility:** All retrieval uses `temperature=0` and fixed seeds. RAGAS evaluation uses `seed=42`. Results are deterministic for the same corpus and configuration.

---

## References

- Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods. *SIGIR '09*.
- Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333–389.
- Shahul, E., et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *arXiv:2309.15217*.
