# 12 · Glossary (quick reference)

Skim this anytime. Terms are grouped by where they appear in the pipeline.

## Core
- **RAG (Retrieval-Augmented Generation)** — retrieve relevant text from your data and put it in the prompt so the LLM answers from facts you supplied.
- **Grounding** — forcing the answer to come only from retrieved context.
- **Hallucination** — confident output not supported by the context.
- **Context window** — max tokens an LLM can read at once.
- **Token** — sub-word unit LLMs process; billing and limits are per token.
- **Provenance / citation** — pointer from a claim back to its source chunk.

## Indexing
- **Loader** — extracts raw text from a source (PDF, HTML, DB).
- **Chunk** — a piece of a document; the unit of retrieval.
- **Chunking** — strategy for splitting docs (fixed, overlap, recursive, structure-aware, semantic).
- **Overlap** — repeated text between adjacent chunks so boundary-straddling facts survive.
- **Metadata** — fields stored with a chunk (source, page, date, permissions) for citations, filtering, access control.
- **Upsert** — insert-or-update a record (used to keep the index fresh idempotently).

## Embeddings & vectors
- **Embedding / vector** — numeric representation of meaning; similar text → nearby vectors.
- **Dimension** — length of the vector (e.g., 1536 for `text-embedding-3-small`).
- **Cosine similarity** — angle-based closeness (−1…1); default for text.
- **Dot product** — cosine × magnitudes; equals cosine for normalized vectors.
- **Euclidean (L2)** — straight-line distance; smaller = closer.
- **Matryoshka embeddings** — truncate a vector to fewer dims to trade accuracy for size.
- **Bi-encoder** — encodes query and doc separately; fast; used for first-pass search.

## Vector databases
- **ANN (Approximate Nearest Neighbor)** — fast, slightly-inexact similarity search.
- **HNSW** — graph ANN index; fast, high recall, handles updates; modern default.
- **IVF / IVF-PQ** — cluster-based ANN; memory-efficient at huge scale; PQ = quantization compression.
- **Recall** — fraction of truly relevant items the search actually returns.
- **ef_search / nprobe** — query-time effort dials for HNSW / IVF (higher = better recall, slower).
- **Pre/post-filter** — apply metadata filters before/after ANN search.

## Retrieval
- **Top-k** — number of chunks retrieved per query.
- **Dense retrieval** — vector/semantic search.
- **Sparse retrieval / BM25** — keyword search; great for exact terms, codes, names.
- **Hybrid retrieval** — dense + sparse combined; 2026 default.
- **RRF (Reciprocal Rank Fusion)** — merges ranked lists by rank, ignoring score scales.
- **Reranking** — re-scoring candidates with a heavier model to reorder them.
- **Cross-encoder** — reranker that reads query+chunk together; accurate but slow.
- **MMR (Maximal Marginal Relevance)** — trades some relevance for diversity to avoid duplicate chunks.
- **Lost in the middle** — LLMs under-attend to facts in the middle of long context.

## Generation
- **Prompt template** — structured instruction + context + question.
- **Relevance gate** — refuse to answer if top retrieval score is below a threshold.
- **Refusal / "I don't know"** — safe exit when context lacks the answer.
- **Temperature** — randomness dial; 0 for factual RAG.
- **Structured output** — model returns JSON for downstream systems.

## Evaluation
- **RAGAS** — RAG evaluation library using LLM-as-judge.
- **Faithfulness** — answer claims supported by context (anti-hallucination).
- **Answer relevancy** — answer addresses the question.
- **Context precision** — retrieved chunks are relevant & well-ranked.
- **Context recall** — retrieval fetched all needed info (needs ground truth).
- **Golden dataset** — reviewed (question, ground-truth answer) test set.
- **LLM-as-judge** — using an LLM to score outputs against a rubric.
- **nDCG / MRR / hit-rate@k** — classic information-retrieval ranking metrics.
- **Online evaluation** — scoring sampled real traffic continuously.

## Advanced & agentic
- **HyDE** — embed a hypothetical answer to retrieve better.
- **Multi-query** — retrieve with several LLM-generated rephrasings.
- **Query decomposition** — split a complex query into sub-queries.
- **Parent-document / small-to-big** — match on small chunks, return big ones.
- **Contextual retrieval** — prepend an LLM-written situating sentence before embedding a chunk.
- **Contextual compression** — strip retrieved chunks to only query-relevant sentences.
- **Adaptive RAG / routing** — classify a query and send it to the cheapest sufficient pipeline.
- **Agentic RAG** — retrieval as a decision loop (route, retrieve iteratively, use tools, self-correct).
- **ReAct** — Reason+Act agent loop (thought → action → observation → …).
- **CRAG (Corrective RAG)** — grade retrieval/answer and self-correct or re-retrieve.
- **Tool use** — agent calling calculators, SQL/APIs, web search, other indexes.

## Graph
- **Knowledge graph** — entities (nodes) + relationships (edges).
- **Triple** — `(subject, relation, object)` extracted from text.
- **Multi-hop** — answer requires chaining several facts.
- **Entity resolution** — merging different mentions of the same entity.
- **Community summary** — LLM summary of a graph cluster, used for global questions (GraphRAG).

## Production
- **Indexing vs query pipeline** — offline ingestion vs online serving, kept separate.
- **TTFT** — time-to-first-token.
- **p50/p90/p99** — latency percentiles.
- **Semantic cache** — return a prior answer when a new query is similar enough.
- **Tracing / observability** — per-request capture of every stage for debugging.
- **Guardrails** — input/output safety checks (prompt injection, PII, toxicity, grounding).
- **Prompt injection** — malicious instructions hidden in retrieved documents.
- **NFR (non-functional requirement)** — latency, scale, cost, reliability, security, compliance targets.
- **Build vs buy** — custom stack vs managed RAG service.

➡️ You've finished the textbook. The rest is reps: build the projects, measure, and rehearse the interview prep.
