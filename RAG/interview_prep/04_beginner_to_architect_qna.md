# RAG Interview Prep: Beginner to Architect Q&A

Use this file as a progressive drill. Start with Beginner, then move down one level only when you can answer most questions out loud without reading.

Interview habit: answer in this shape whenever possible:

1. Direct answer.
2. Why it matters.
3. Trade-off or failure mode.
4. How you would measure or debug it.

---

## Level 1: Beginner

### 1. What is RAG?

RAG means Retrieval-Augmented Generation. Before the LLM answers, the system retrieves relevant information from a knowledge source and puts that context into the prompt. The model then answers using the retrieved context instead of relying only on its training data.

### 2. Why do we use RAG?

We use RAG to answer questions using private, fresh, or domain-specific data. It helps reduce hallucination, gives citations, and avoids retraining the model every time the data changes.

### 3. What are the main stages of a RAG system?

The main stages are indexing, retrieval, and generation. Indexing prepares documents by loading, chunking, embedding, and storing them. Retrieval finds relevant chunks for a user query. Generation uses those chunks to produce the final answer.

### 4. What is a document chunk?

A chunk is a smaller piece of a document used as the unit of retrieval. Instead of embedding a whole PDF or page, the system splits content into meaningful pieces so the retriever can find the exact information needed.

### 5. Why not embed the whole document as one vector?

A whole document usually contains many topics, so one vector becomes too general. Retrieval becomes weak because the vector represents an average of the document instead of a specific fact or section.

### 6. What is an embedding?

An embedding is a list of numbers that represents the meaning of text. Texts with similar meanings have vectors that are close to each other, which allows semantic search.

### 7. What is a vector database?

A vector database stores embeddings, the original text, and metadata. It supports fast similarity search so the system can find chunks close to the query embedding.

### 8. What is semantic search?

Semantic search finds text based on meaning rather than exact keyword match. For example, "refund policy" and "how do I get my money back" may match even if they use different words.

### 9. What is top-k retrieval?

Top-k retrieval means returning the k most relevant chunks from the search step. If k is too small, the system may miss important context. If k is too large, the prompt may become noisy and expensive.

### 10. What is grounding?

Grounding means forcing the LLM answer to be based on retrieved context. A grounded answer should be supported by the source documents, not invented from model memory.

### 11. What is a hallucination in RAG?

A hallucination is an answer that sounds confident but is not supported by the retrieved context. RAG reduces hallucination but does not eliminate it automatically.

### 12. Why are citations important in RAG?

Citations show where the answer came from. They help users verify claims and help developers debug whether the correct chunks were retrieved.

### 13. What is the difference between RAG and fine-tuning?

RAG adds facts at query time by retrieving documents. Fine-tuning changes model behavior or style by training on examples. A simple interview line is: use RAG for knowledge, fine-tuning for behavior.

### 14. What is the difference between RAG and long-context prompting?

Long-context prompting puts a lot of content directly into the prompt. RAG first selects the most relevant content and only sends that. RAG is usually cheaper and more scalable for large or changing corpora.

### 15. What should a basic RAG prompt contain?

It should contain system instructions, retrieved context, the user question, and rules such as "answer only from the context", "cite sources", and "say you do not know if the answer is missing".

### 16. What does "I do not know" mean in a good RAG system?

It means the system did not find enough reliable context to answer. This is better than guessing, especially in enterprise, legal, medical, finance, or customer support use cases.

### 17. What metadata should be stored with each chunk?

Common metadata includes source file, page number, URL, title, section heading, timestamp, tenant ID, permissions, and chunk ID. Metadata helps with citations, filtering, freshness, and debugging.

### 18. What is the simplest working RAG pipeline?

Load documents, split them into chunks, embed the chunks, store them in a vector index, embed the user query, retrieve similar chunks, put them into a prompt, and ask the LLM to answer.

### 19. What are common beginner mistakes in RAG?

Common mistakes include chunks that are too large, missing metadata, retrieving too many irrelevant chunks, not using citations, using different embedding models for indexing and querying, and trusting the LLM even when retrieval failed.

### 20. How do you explain RAG in one minute?

RAG is a way to connect an LLM to external knowledge. We prepare documents by chunking and embedding them, retrieve the most relevant chunks for each question, and give those chunks to the LLM so it can answer with citations. It is useful when the knowledge is private, large, or changing.

---

## Level 2: Intermediate

### 21. How do you choose chunk size?

Start with a reasonable default such as a few hundred tokens, then evaluate. Smaller chunks improve precise matching but may lose context. Larger chunks preserve context but can retrieve irrelevant material. The right choice depends on the corpus and metrics.

### 22. What is chunk overlap?

Chunk overlap repeats some tokens between adjacent chunks. It prevents facts near boundaries from being split apart. Too much overlap increases storage, cost, and duplicate retrieval.

### 23. What chunking strategies do you know?

Common strategies are fixed-size chunking, recursive chunking, structure-aware chunking, semantic chunking, and parent-document retrieval. Structure-aware chunking is often better for Markdown, HTML, code, tables, and policy documents.

### 24. What is parent-document retrieval?

The system embeds small chunks for precise search but returns a larger parent section to the LLM. This gives both precise matching and enough surrounding context.

### 25. What is hybrid search?

Hybrid search combines dense vector search with sparse keyword search such as BM25. Dense search captures semantic similarity, while sparse search catches exact names, IDs, codes, dates, and jargon.

### 26. Why is pure vector search sometimes not enough?

Vector search can miss exact terms such as product codes, legal citations, error IDs, or rare names. It may retrieve semantically similar text but miss the exact required fact.

### 27. What is BM25?

BM25 is a sparse keyword-ranking algorithm. It scores documents based on term frequency, inverse document frequency, and document length. It is strong for exact lexical matching.

### 28. What is reranking?

Reranking is a second-stage retrieval step. First, a fast retriever returns many candidates. Then a more accurate model scores the query and each candidate together, producing a better final order.

### 29. What is the difference between a bi-encoder and a cross-encoder?

A bi-encoder embeds the query and document separately, which is fast and scalable. A cross-encoder reads the query and document together, which is more accurate but slower. RAG often uses a bi-encoder for retrieval and a cross-encoder for reranking.

### 30. What is Reciprocal Rank Fusion?

Reciprocal Rank Fusion, or RRF, combines ranked results from multiple retrievers. It uses rank position rather than raw scores, which is helpful because vector and keyword scores are not directly comparable.

### 31. What is query rewriting?

Query rewriting transforms the user question into a better search query. It can expand abbreviations, remove conversational noise, generate alternate phrasings, or decompose a complex question.

### 32. What is multi-query retrieval?

Multi-query retrieval generates several versions of the user's question, retrieves results for each, and merges them. It improves recall when users phrase questions differently from the documents.

### 33. What is HyDE?

HyDE means Hypothetical Document Embeddings. The system asks an LLM to draft a hypothetical answer or passage, embeds that text, and searches with it. It can help when the user query is short or vague, but the hypothetical text can also mislead retrieval if it is wrong.

### 34. What is a relevance threshold?

A relevance threshold is a minimum score required before generating an answer. If retrieved context is too weak, the system should refuse, ask a clarifying question, or route to another tool.

### 35. How do you reduce hallucination in RAG?

Improve retrieval, use a grounded prompt, require citations, add a relevance gate, set low temperature, and evaluate faithfulness. The most important step is to ensure the right context is retrieved.

### 36. What are the main RAG evaluation metrics?

Common metrics include faithfulness, answer relevancy, context precision, and context recall. Context metrics test retrieval quality. Faithfulness and answer relevancy test generation quality.

### 37. What is faithfulness?

Faithfulness measures whether the answer is supported by the retrieved context. A faithful answer does not add unsupported claims.

### 38. What is context precision?

Context precision measures whether the retrieved chunks are relevant and well ranked. Low precision means the system retrieved too much noise.

### 39. What is context recall?

Context recall measures whether the retrieved chunks contain all information needed to answer the question. Low recall means the answer may fail because the system missed required evidence.

### 40. What is a golden dataset?

A golden dataset is a reviewed set of questions, expected answers, and sometimes expected source documents. It is used to test RAG quality consistently during development and CI.

### 41. How do you debug a wrong RAG answer?

Check whether the right source exists in the corpus, whether it was loaded correctly, whether chunking preserved the fact, whether retrieval found it, whether reranking kept it, and whether the LLM used it faithfully.

### 42. What is "lost in the middle"?

Lost in the middle is when an LLM pays less attention to information placed in the middle of a long context. RAG systems reduce this by retrieving fewer, better chunks and putting the most important context first.

### 43. How do you handle tables in RAG?

Preserve table structure during extraction, include useful headers and row labels, store metadata, and consider converting rows or sections into text chunks. For complex numeric analysis, route to a structured query or tool instead of relying only on text retrieval.

### 44. How do you handle PDFs in RAG?

Use a reliable parser, preserve page numbers, headings, tables, and layout when possible, remove headers and footers if they add noise, and validate extraction quality before embedding.

### 45. What is semantic caching?

Semantic caching stores answers and uses embedding similarity to reuse them for similar future queries. It reduces latency and cost but must be invalidated when the underlying documents change.

---

## Level 3: Senior

### 46. How would you design a production RAG architecture?

I would separate indexing and query pipelines. The indexing pipeline loads, cleans, chunks, embeds, and upserts documents with metadata. The query pipeline authenticates the user, applies guardrails, retrieves with filters, reranks, builds a grounded prompt, generates a cited answer, validates output, logs traces, and returns the response.

### 47. Why separate indexing from querying?

They have different workloads and latency needs. Indexing can be batch or event-driven and may be expensive. Querying must be fast and reliable. Separating them prevents document ingestion from slowing user requests.

### 48. How do you keep a RAG index fresh?

Use event-driven or scheduled ingestion, stable document and chunk IDs, idempotent upserts, deletion handling, cache invalidation, and freshness monitoring. Define a freshness SLA, such as "new documents searchable within five minutes".

### 49. How do you enforce access control?

Store tenant, user, role, or ACL metadata on every chunk and apply authorization as a pre-filter during retrieval. Never rely on the prompt to hide unauthorized documents.

### 50. How do you prevent cross-tenant data leakage?

Use strict metadata filters, tenant-isolated indexes when needed, access-control tests, trace audits, and cache keys that include tenant and permission scope. Shared semantic caches must be designed carefully to avoid leaking answers.

### 51. How do you handle prompt injection in retrieved documents?

Treat retrieved content as untrusted data, not instructions. The system prompt should say that document text is evidence only. Also restrict tools, sanitize content, use output checks, and monitor suspicious patterns.

### 52. What should be logged in a RAG trace?

Log the user query, route chosen, retrieved chunk IDs, scores, metadata filters, reranked order, prompt version, model, token counts, latency per stage, cost, answer, citations, and guardrail decisions. Avoid storing sensitive data unless approved.

### 53. What RAG metrics would you monitor in production?

Monitor latency percentiles, time to first token, retrieval latency, generation latency, cache hit rate, refusal rate, escalation rate, token cost, retrieval precision signals, user feedback, and online evaluation scores.

### 54. How do you optimize RAG latency?

Use caching, parallel retrieval, faster embedding and reranking models, retrieve fewer chunks, stream the response, use model tiering, reduce prompt size, and trace stage-level latency to find the bottleneck.

### 55. How do you optimize RAG cost?

Reduce tokens, use smaller models where possible, cache repeated queries, route easy queries to cheaper paths, batch indexing jobs, avoid unnecessary multi-query or agent loops, and evaluate whether each quality improvement is worth its cost.

### 56. What is adaptive RAG?

Adaptive RAG routes each query to the cheapest sufficient path. Some questions may need no retrieval, some need simple retrieval, some need hybrid plus reranking, and some need multi-step or tool-based reasoning.

### 57. What is corrective RAG?

Corrective RAG checks whether retrieved context is good enough. If not, it rewrites the query, retrieves again, uses another source, asks a clarification, or refuses.

### 58. What is agentic RAG?

Agentic RAG lets an LLM decide when to retrieve, which tools to call, whether results are sufficient, and whether to retrieve again. It is useful for complex workflows but increases latency, cost, and operational risk.

### 59. When should you avoid agentic RAG?

Avoid it when a simple fixed pipeline answers most questions well. Agentic loops add complexity, nondeterminism, and cost. Add them only for measured failure cases that require planning or multi-step tool use.

### 60. How do you evaluate a change to retrieval?

Run it against a golden dataset and compare context precision, context recall, answer quality, latency, and cost. Change one variable at a time so you know what caused the improvement or regression.

### 61. How do you evaluate a change to the prompt?

Keep retrieval fixed and compare faithfulness, answer relevancy, citation accuracy, refusal behavior, and formatting correctness. Prompts should be versioned and tested like code.

### 62. What is A/B testing in RAG?

A/B testing sends production traffic to two different versions and compares metrics such as user satisfaction, answer quality, refusal rate, latency, and cost. It is useful after offline evaluation but must be monitored carefully.

### 63. How do you handle multilingual RAG?

Choose multilingual embeddings or route by language, preserve language metadata, retrieve across the correct language scope, and decide whether to answer in the user's language or the source language. Evaluate per language, not only globally.

### 64. How do you handle frequently changing documents?

Use incremental indexing, document versioning, stable IDs, update timestamps, tombstones for deletes, and cache invalidation. The query path should know whether it is allowed to use stale data.

### 65. How do you handle duplicate or near-duplicate chunks?

Deduplicate during ingestion, use canonical sources, apply Maximal Marginal Relevance or diversity-aware retrieval, and avoid stuffing the prompt with repeated evidence.

### 66. What is Maximal Marginal Relevance?

Maximal Marginal Relevance balances relevance and diversity. It helps when top retrieved chunks are all similar and the answer needs broader coverage.

### 67. How would you handle conflicting documents?

Use metadata such as timestamp, authority, source type, and version. The generation prompt should mention conflicts and cite both sources when needed. For high-stakes systems, define source-of-truth rules.

### 68. How do you design citations?

Attach source metadata to every chunk, label chunks in the prompt, instruct the model to cite those labels, and validate that cited labels exist. The UI should map citations back to document, page, URL, or section.

### 69. What is structured output in RAG?

Structured output asks the model to return fields such as answer, citations, confidence, missing information, and follow-up question. It is useful when downstream systems consume the response.

### 70. What are common production failure modes?

Common failures include stale indexes, bad PDF extraction, missing ACL filters, prompt injection, cache leakage, noisy retrieval, low recall, hallucinated citations, high latency, rising token cost, and silent quality regressions.

---

## Level 4: Architect

### 71. Design a RAG system for internal company documents.

I would clarify corpus size, document types, update rate, users, permissions, latency, and citation requirements. Architecture: event-driven indexing pipeline, vector plus keyword index, metadata ACL filters, hybrid retrieval, reranking, grounded generation with citations, semantic cache, observability, offline golden-set evaluation, and online feedback. The key design decision is enforcing permissions before retrieval and keeping indexing independent from the query path.

### 72. Design a RAG system for customer support.

I would optimize for correctness, low cost, safe refusal, and escalation. Use curated product docs as the primary source, past tickets only if sanitized and permissioned, hybrid retrieval, reranking, grounded answers, low-confidence escalation, abuse and injection guardrails, semantic caching, and human handoff. Track resolution rate, hallucination rate, escalation precision, latency, and cost per conversation.

### 73. Design a RAG system for legal documents.

Legal RAG needs high precision, exact citations, strong access control, audit logs, versioning, and conservative refusal. I would use structure-aware chunking, hybrid search for exact citations, reranking, source authority metadata, document version control, and human review for high-risk workflows.

### 74. Design a RAG system for millions of documents.

At large scale, I would focus on indexing throughput, sharding, metadata filters, approximate nearest-neighbor search, hybrid retrieval, caching, observability, and incremental updates. I would also partition by tenant or domain where appropriate and evaluate recall under realistic latency targets.

### 75. How do you choose between pgvector, a dedicated vector DB, and a managed service?

Use pgvector when the team already runs Postgres and scale is moderate. Use a dedicated vector DB when you need stronger vector performance, filtering, hybrid search, or scale. Use a managed service when time-to-market and low ops matter more than deep control. The answer depends on scale, team skills, compliance, cost, and customization.

### 76. What is the role of a knowledge graph in RAG?

A knowledge graph stores entities and relationships. It helps with multi-hop, relationship-heavy, and global questions that vector search may miss. It is expensive to build and maintain, so I would use it only when relational reasoning is central to the product.

### 77. What is Graph RAG?

Graph RAG combines graph-based retrieval with generation. The system extracts entities and relationships, retrieves relevant graph neighborhoods or summaries, and gives them to the LLM. It is useful for questions like "who owns the system that depends on this service?"

### 78. What is the difference between local and global retrieval in Graph RAG?

Local retrieval starts from entities in the query and traverses nearby relationships. Global retrieval answers broad questions by using higher-level summaries, communities, or graph-wide aggregations.

### 79. How do you design a RAG evaluation program?

Build a golden dataset, separate retrieval and generation metrics, run offline eval in CI, sample production traffic for online eval, capture human feedback, add regression thresholds, and review failures regularly. Evaluation should become part of the release process.

### 80. How do you answer "our RAG is bad, fix it"?

I would first define what "bad" means: wrong answer, missing answer, hallucination, latency, cost, or UX. Then I would inspect traces, run the golden set, localize the issue to ingestion, retrieval, reranking, prompting, model behavior, or freshness, make one change, and measure again.

### 81. How do you handle "the answer is correct but slow"?

Trace latency by stage. If retrieval is slow, tune indexes, filters, and top-k. If reranking is slow, rerank fewer candidates or use a faster model. If generation is slow, reduce context tokens, use a smaller model, stream output, or cache. Optimize the measured bottleneck.

### 82. How do you handle "the answer is fast but wrong"?

Check if the correct evidence exists, whether it was extracted, chunked, embedded, retrieved, reranked, and included in the prompt. If evidence was included but not used, fix the prompt or model. If evidence was missing, fix retrieval or ingestion.

### 83. How do you handle "the system gives answers without evidence"?

Add stricter grounding instructions, citation requirements, relevance thresholds, output validation, and refusal behavior. Also improve retrieval so the model has enough evidence. A prompt alone cannot compensate for missing context.

### 84. How do you design for right to be forgotten?

Use stable document IDs, chunk IDs, metadata lineage, delete propagation, embedding deletion, cache purge, and audit logs. The system must delete both raw documents and derived artifacts such as chunks, embeddings, summaries, and cached answers.

### 85. How do you design for regulated data?

Apply least-privilege access, encryption, audit logs, data retention rules, PII redaction, tenant isolation, region controls, approved model providers, and human review for high-risk outputs. Evaluation should include safety and compliance cases.

### 86. How do you manage model upgrades in RAG?

Version prompts, embedding models, rerankers, and generation models. Re-embed if the embedding model changes. Run offline eval, compare latency and cost, canary in production, monitor regressions, and keep rollback paths.

### 87. How do you manage embedding model changes?

Because old and new embedding spaces are not compatible, create a new index or dual-write during migration. Evaluate retrieval quality before switching traffic. Plan storage and backfill time.

### 88. How would you build a multi-tenant RAG SaaS?

Use tenant-aware ingestion, tenant metadata on every chunk, strict pre-filtering, tenant-scoped cache keys, per-tenant quotas, observability by tenant, and isolation for sensitive customers. For high-risk tenants, separate indexes or infrastructure may be justified.

### 89. How do you decide whether to use RAG, fine-tuning, or both?

Use RAG for facts that change or live outside the model. Use fine-tuning for behavior, format, tone, or repeated task patterns. Use both when the assistant needs specialized behavior and access to fresh knowledge.

### 90. How do you defend a RAG design in an architect interview?

Clarify requirements, draw both indexing and query pipelines, explain retrieval and generation choices, state trade-offs, give numbers for latency/cost/quality targets, cover security and operations, and describe evaluation. The interviewer is testing judgment, not tool memorization.

### 91. What trade-offs do you mention for hybrid retrieval?

Hybrid improves recall, especially for exact terms, but adds index complexity and query-time work. I would use it when the corpus has codes, names, product IDs, legal citations, or jargon, and validate the recall improvement against latency and cost.

### 92. What trade-offs do you mention for reranking?

Reranking usually improves precision but adds latency and cost. A common design is to retrieve many candidates cheaply, rerank only the top candidates, and send a small final context to the LLM.

### 93. What trade-offs do you mention for semantic caching?

Semantic caching reduces latency and cost but risks stale or incorrect reuse. It needs similarity thresholds, tenant-aware keys, source-version awareness, and invalidation when documents change.

### 94. What trade-offs do you mention for larger context windows?

Larger context windows let you include more evidence but increase cost, latency, and the chance of irrelevant context. They do not remove the need for good retrieval.

### 95. What trade-offs do you mention for agents?

Agents can solve complex, multi-step tasks but increase latency, cost, nondeterminism, and observability needs. Use step limits, tool permissions, fallbacks, and tracing.

### 96. How do you create an interview-ready RAG answer?

Start with the simple answer, then add nuance. For example: "I would use hybrid retrieval plus reranking. Dense search catches semantic matches, BM25 catches exact terms, and reranking improves final precision. The trade-off is latency, so I would measure context precision and p90 latency before shipping."

### 97. What numbers should you be ready to discuss?

Be ready to discuss chunk size ranges, top-k values, latency percentiles, cost per query, golden dataset size, cache hit rate, retrieval precision and recall, faithfulness, refusal rate, and freshness SLA. Exact numbers depend on the project, but architects should think in measurable targets.

### 98. What is the best answer to "it depends"?

"It depends" is acceptable only if you say what it depends on. For example: "It depends on corpus size, update rate, latency target, access-control requirements, and whether exact keyword matching matters."

### 99. How do you show seniority in RAG interviews?

Show that you can diagnose systems, not just name techniques. Talk about traces, evals, trade-offs, security, cost, latency, and rollback. Avoid adding advanced patterns unless a measured failure justifies them.

### 100. Give a complete architect-level summary of RAG.

A production RAG system has two main pipelines. The indexing pipeline converts source documents into searchable chunks with embeddings and metadata. The query pipeline authenticates the user, retrieves authorized relevant context, reranks it, builds a grounded prompt, generates a cited answer, validates it, and logs everything. Quality depends on ingestion, chunking, retrieval, prompting, evaluation, and operations. Architect-level RAG is about making the system correct, secure, fresh, observable, scalable, and cost-effective.

---

## Final Mock Drill

Answer these without reading the model answers:

1. Explain RAG to a beginner.
2. Compare RAG, fine-tuning, and long context.
3. Draw the indexing and query pipelines.
4. Debug a wrong answer.
5. Debug a slow answer.
6. Design RAG for internal documents with permissions.
7. Design RAG for customer support with escalation.
8. Explain hybrid retrieval and reranking with trade-offs.
9. Explain how you evaluate RAG.
10. Explain how you secure a multi-tenant RAG system.

If you can answer all ten clearly, with trade-offs and metrics, you are ready for senior and architect-level RAG interviews.
