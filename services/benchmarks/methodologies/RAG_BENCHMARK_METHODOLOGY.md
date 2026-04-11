# RAG Retrieval Benchmarking Methodology

---

## 1. What Is Being Evaluated

This benchmark evaluates **retrieval quality** — whether the RAG pipeline retrieves text chunks that contain the knowledge needed to generate a correct quiz question. It does not evaluate the language model's question generation quality, which is benchmarked separately in the LLM generation pipeline.

The distinction matters because retrieval and generation are independent failure modes. A perfect language model will still produce a bad question if it receives irrelevant chunks. Conversely, a weaker model can produce an adequate question if the retrieved context is on-topic. Isolating retrieval quality from generation quality allows each component to be optimised and diagnosed independently.

### Why retrieval configuration is not trivial

The WLA corpus is heterogeneous: it contains practitioner guides written in accessible, directive language (e.g. Anna Freud National Centre materials) alongside peer-reviewed research papers with formal academic vocabulary (e.g. Schlesier et al. 2023, Johnson et al. 2023). A retrieval configuration that works well for one writing style may underperform for the other. The benchmark is designed to surface these differences by including golden questions sourced from both document types.

---

## 2. Configuration Matrix

The benchmark tests all combinations of three independent variables:

| Variable | Values | Rationale |
|----------|--------|-----------|
| Embedding model | `all-MiniLM-L6-v2` (baseline), `all-mpnet-base-v2`, `bge-small-en-v1.5` | Three widely-used sentence transformer models of varying size and architecture. MiniLM is the production default; mpnet offers higher dimensionality (768 vs 384); BGE represents a different training objective (contrastive learning with instruction tuning). |
| Chunk size / overlap | 512/50, 800/100 | 800/100 is the production baseline. 512/50 tests whether smaller, more focused chunks improve precision at the cost of losing cross-sentence context. Larger sizes (1024/200) were excluded because preliminary testing showed diminishing returns with the corpus's average paragraph length. |
| Retrieval strategy | Dense (cosine similarity), Hybrid (BM25 + dense via RRF) | Dense retrieval is the production default. Hybrid retrieval adds lexical matching via BM25 to complement semantic similarity, combined through Reciprocal Rank Fusion (Cormack et al., 2009). |

This produces **12 configurations** (3 models × 2 chunk sizes × 2 retrieval types).

### Why these specific models

- **all-MiniLM-L6-v2:** Production baseline. Fastest inference, smallest memory footprint. Included as the control against which all other models are compared.
- **all-mpnet-base-v2:** Higher-dimensional embeddings (768D vs 384D) with stronger performance on semantic textual similarity benchmarks (Reimers & Gurevych, 2019). Tests whether richer representations improve retrieval for this domain.
- **bge-small-en-v1.5:** Trained with instruction-aware contrastive learning (Xiao et al., 2023). Tests whether a model explicitly trained for retrieval tasks outperforms general-purpose sentence transformers on this corpus.

### Why hybrid retrieval

Dense retrieval finds semantically similar chunks but can miss chunks that contain the exact terminology used in the question. BM25 (Robertson & Zaragoza, 2009) provides exact keyword matching that complements semantic search. The two are combined via Reciprocal Rank Fusion (RRF, k=60), which merges ranked lists without requiring score normalisation across different retrieval methods. RRF was chosen over learned re-ranking because it is parameter-free and deterministic — important for reproducibility.

The `rank_bm25` library is used for the BM25 component. RRF determines chunk ordering; the cosine similarity score from dense retrieval is preserved as the quality metric.

---

## 3. Golden Question Set

### Design principles

The evaluation uses 10 manually curated questions, each:

1. **Grounded in a specific corpus passage** — the answer must exist verbatim or paraphrased in an identified PDF
2. **Paired with a ground-truth answer** — extracted from the source passage and verified by the researcher
3. **Tagged with taxonomy keywords** — matching the platform's keyword hierarchy in `keywords.yaml`, ensuring the benchmark uses the same retrieval path as the production system
4. **Spanning both document types** — practitioner guides and academic papers, to test retrieval across the corpus's heterogeneous writing styles

### Why 10 questions

The golden set is intentionally small for the following reasons:

- Each question requires manual verification against the source PDF, making large sets impractical for a single researcher
- The benchmark runs each question against 12 configurations, producing 120 evaluation rows — sufficient to identify consistent trends across configurations
- RAGAS evaluation requires an LLM judge call per question per configuration, making larger sets computationally expensive with local inference

The trade-off is that 10 questions is insufficient for statistical significance testing. The benchmark identifies consistent trends and directional findings, not statistically rigorous claims. A larger golden set (50+) would be needed for significance testing and is noted as future work.

### Curation process

Questions were initially drafted with AI assistance, then each question and its ground-truth answer were individually verified by the researcher against the cited PDF passage. This human-in-the-loop curation ensures factual accuracy and source traceability while using AI to accelerate the drafting of plausible question formats.

---

## 4. Evaluation Metrics

### Cosine similarity (top_score)

The retrieval system's native scoring mechanism. Measures how semantically similar the top retrieved chunk is to the query embedding. Values close to 1.0 indicate high semantic similarity.

**Limitation:** A chunk can be semantically similar to a question without containing the answer. For example, a chunk about "school anxiety research methodology" will score high cosine similarity against a question about "school anxiety interventions" because both share the same domain vocabulary. This metric alone cannot distinguish topical relevance from answer relevance.

### RAGAS context_precision

An LLM-judged metric from the RAGAS framework (Shahul et al., 2023) that assesses whether the retrieved chunks contain the knowledge needed to answer the question. Scored 0–1, where 1.0 means the retrieved context fully supports the ground-truth answer.

This metric addresses the limitation of cosine similarity by using a language model to judge whether the retrieved context actually answers the question, not just whether it is topically related.

**Evaluation LLM:** Mistral 7B Instruct (Q4_0 quantisation) via local Ollama. Using the production model as the RAGAS judge creates a potential self-assessment bias — the same model that would generate questions from these chunks is also judging their relevance. This was accepted as a pragmatic trade-off for Phase 6: the LLM generation benchmark (Phase 7) addresses this by using a separate, larger judge model (Google Gemini 1.5 Flash).

**Evaluation configuration:** Sequential evaluation (`max_workers=1`) against a local Ollama instance. Batch evaluation per configuration (10 questions per RAGAS call) rather than individual calls, reducing Ollama overhead.

---

## 5. Output Format

Results are written to `results/rag_YYYYMMDD_HHMMSS.csv` — one row per question per configuration (120 rows total).

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | ISO 8601 | UTC timestamp of the evaluation run |
| `emb_model` | string | Full embedding model identifier |
| `chunk_size` | int | Token count per chunk |
| `chunk_overlap` | int | Overlap tokens between consecutive chunks |
| `retrieval_type` | string | `dense` or `hybrid` |
| `question` | string | Golden question text |
| `ground_truth` | string | Expected answer, verified against source PDF |
| `keywords_used` | string | Taxonomy keywords used for retrieval (`|`-delimited) |
| `num_contexts` | int | Number of chunks retrieved |
| `contexts_text` | string | Actual retrieved chunk text (`|||`-delimited) |
| `top_score` | float | Cosine similarity of the top-ranked retrieved chunk |
| `context_relevancy` | float/null | RAGAS context_precision score (0–1) |

### Why the CSV includes full chunk text

The `contexts_text` column preserves the actual retrieved text so that the downstream LLM generation benchmark can operate on frozen retrieval results. This decoupled architecture means:

- The LLM benchmark does not need access to ChromaDB
- Generation quality is evaluated against the exact same chunks, eliminating retrieval as a confounding variable
- Results are fully reproducible from the CSV alone, without needing to re-run the retrieval pipeline

The `|||` delimiter was chosen because pipe (`|`) appears in chunk text (used in tables and lists within the source PDFs), while triple-pipe does not.

---

## 6. Reproducibility

- All retrieval uses `temperature=0` and fixed seeds
- RAGAS evaluation uses `seed=42`
- Ingestion is forced (`force=True`) for each configuration to ensure a clean collection state
- Results are deterministic for the same corpus, configuration, and embedding model version

---

## References

- Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods. *SIGIR '09*.
- Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP 2019*.
- Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333–389.
- Shahul, E., et al. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation. *arXiv:2309.15217*.
- Xiao, S., et al. (2023). C-Pack: Packaged Resources To Advance General Chinese Embedding. *arXiv:2309.07597*.
