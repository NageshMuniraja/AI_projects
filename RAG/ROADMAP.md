# The 14-Day RAG Roadmap (Beginner → Architect)

~3 hours/day. Each day = **read** (docs), **build** (project), **review** (interview prep).
Two weeks, two phases. Week 1 = build solid fundamentals + a working, measurable pipeline. Week 2 = advanced patterns, production, and interview mastery.

Legend: 📖 read · 🛠️ build · 🎯 interview review · 🧪 stretch

---

## WEEK 1 — Fundamentals & a measurable pipeline

### Day 1 — What RAG is and why it exists
- 📖 `docs/01_rag_fundamentals.md`
- 🛠️ `projects/01_hello_rag` — build a RAG loop from scratch (no framework): chunk a text file, embed, cosine-similarity search, stuff context, answer.
- 🎯 Interview Q&A §1 (Fundamentals): "What problem does RAG solve vs fine-tuning vs long context?"
- 🧪 Make `hello_rag` answer "I don't know" when the context doesn't contain the answer.

### Day 2 — Embeddings & vector math
- 📖 `docs/02_embeddings_and_vectors.md`
- 🛠️ Re-run `01_hello_rag` experiments: print similarity scores, try different queries, visualize which chunks win and why.
- 🎯 Interview Q&A §2 (Embeddings): cosine vs dot vs Euclidean; what an embedding actually encodes.
- 🧪 Swap `text-embedding-3-small` → `text-embedding-3-large` and compare retrieved chunks.

### Day 3 — Chunking
- 📖 `docs/03_chunking_strategies.md`
- 🛠️ `projects/03_chunking_lab` — load a long document, try fixed/recursive/sentence/semantic chunking, eyeball retrieval quality.
- 🎯 Interview Q&A §3 (Chunking): "80% of RAG failures start in ingestion — why?"
- 🧪 Find a question that only works with one chunking strategy and not the others.

### Day 4 — Vector databases
- 📖 `docs/04_vector_databases.md`
- 🛠️ `projects/02_pdf_qa` — real PDF Q&A with **Chroma** as a persistent vector store, returning **citations** (source page/chunk).
- 🎯 Interview Q&A §4 (Vector DBs): HNSW vs IVF, when to use pgvector vs Pinecone vs Qdrant.
- 🧪 Add metadata filtering (e.g., only search within one document or section).

### Day 5 — Retrieval strategies (the big one)
- 📖 `docs/05_retrieval_strategies.md`
- 🛠️ `projects/04_hybrid_search` — combine **BM25 (keyword)** + **vector** search, fuse with **Reciprocal Rank Fusion**, then **rerank** with a cross-encoder.
- 🎯 Interview Q&A §5 (Retrieval): why hybrid beats pure vector; what reranking fixes.
- 🧪 Build a query where keyword search wins and one where vector search wins; show RRF gets both.

### Day 6 — Generation & prompting
- 📖 `docs/06_generation_and_prompting.md`
- 🛠️ Harden `02_pdf_qa`: add a grounded prompt template, citation formatting, and refusal behavior; reduce hallucination.
- 🎯 Interview Q&A §6 (Generation): context-window packing, "lost in the middle", citation enforcement.
- 🧪 Add a "context relevance" guard: if top score < threshold, refuse instead of guessing.

### Day 7 — Evaluation (this is what makes you senior)
- 📖 `docs/07_evaluation_ragas.md`
- 🛠️ `projects/05_eval_harness` — build a golden dataset and score faithfulness, answer relevancy, context precision/recall with **RAGAS**.
- 🎯 Interview Q&A §7 (Evaluation): the four core RAGAS metrics and what each failure looks like.
- 🧪 Use the eval harness to prove that hybrid+rerank (Day 5) beats naive retrieval (Day 1) with numbers.

**End of Week 1 checkpoint:** you can build a RAG system, retrieve well, and *prove* it works. You're now past "tutorial level."

---

## WEEK 2 — Advanced patterns, production, and interview mastery

### Day 8 — Advanced RAG techniques
- 📖 `docs/08_advanced_rag.md`
- 🛠️ Add query transformations to `04_hybrid_search`: multi-query expansion, HyDE, and a contextual-compression step.
- 🎯 Interview Q&A §8 (Advanced): HyDE, query decomposition, parent-document retrieval, contextual retrieval.
- 🧪 Measure each technique in the eval harness — keep only the ones that actually move the score.

### Day 9 — Agentic RAG, part 1 (routing)
- 📖 `docs/09_agentic_rag.md` (first half)
- 🛠️ `projects/06_agentic_rag` — build an **adaptive router**: classify each query (simple lookup / multi-hop / out-of-scope) and send it down the right pipeline.
- 🎯 Interview Q&A §9 (Agentic): when an agent loop is worth the latency/cost.
- 🧪 Add a "no retrieval needed" path so chit-chat doesn't hit the vector DB.

### Day 10 — Agentic RAG, part 2 (multi-step + tools)
- 📖 `docs/09_agentic_rag.md` (second half)
- 🛠️ Extend `06_agentic_rag`: iterative retrieve→reason→retrieve loop, plus a tool (e.g., calculator or web/SQL stub) the agent can call.
- 🎯 Interview Q&A §9 cont.: self-correction, reflection, guarding against infinite loops.
- 🧪 Add a max-steps budget and a fallback answer when the agent can't converge.

### Day 11 — Graph RAG
- 📖 `docs/10_graph_rag.md`
- 🛠️ `projects/07_graph_rag` — extract entities/relationships, build a small knowledge graph, and answer multi-hop questions vector search alone can't.
- 🎯 Interview Q&A §10 (Graph): when graph beats vectors; GraphRAG community summaries.
- 🧪 Find a multi-hop question ("who reports to the person who owns X?") that only graph retrieval answers correctly.

### Day 12 — Production architecture
- 📖 `docs/11_production_architecture.md`
- 🛠️ `projects/08_production_rag` — wrap your best pipeline in a **FastAPI** service: `/ingest` and `/query` endpoints, request/response models, streaming.
- 🎯 Interview Q&A §11 (Production): separated indexing vs query pipelines, latency budgets, SLAs.
- 🧪 Add semantic caching so repeated/similar queries return instantly.

### Day 13 — Production hardening
- 📖 `docs/11_production_architecture.md` (re-read the "non-functional requirements" section)
- 🛠️ Add to `08_production_rag`: structured logging + tracing, guardrails (PII/prompt-injection check), rate limiting, and a Dockerfile.
- 🎯 Interview Q&A §11 cont.: observability, cost control, security, evaluation-in-CI.
- 🧪 Add an online eval hook that samples real queries and scores them nightly.

### Day 14 — Architect interview simulation
- 📖 `interview_prep/02_system_design_playbook.md`
- 🛠️ Do the full design exercise: *"Design a RAG assistant over 10k constantly-updated internal docs, 1,000 concurrent users, <2s p90 latency, with citations."* Whiteboard it end-to-end.
- 🎯 Take the **mock interview** in the playbook; answer out loud; compare to the model answers.
- 🧪 Record yourself defending three trade-offs (chunking, retrieval, build-vs-buy). If you can defend them cleanly, you're at architect level.

---

## Pace adjustments

- **Tight on time?** Do the 📖 + 🛠️ each day and push 🧪 stretch goals to the weekend.
- **Have extra time?** The stretch goals and the second half of the question bank are where real depth lives.
- **Falling behind on a build?** Each project README has a "Minimum viable" and a "Full version." Ship minimum, move on, circle back.

## Definition of "done = architect level"

You can: (1) draw the full pipeline from memory, (2) name a metric for every component, (3) justify every default with a trade-off, and (4) take a vague business requirement and turn it into a concrete, costed, observable design. Days 7, 12, and 14 are where this clicks.
