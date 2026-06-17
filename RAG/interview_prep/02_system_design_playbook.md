# RAG System-Design Playbook (Architect Round)

The architect interview is rarely "define RAG." It's "design a RAG system for X under these constraints, and defend every decision." This playbook gives you a repeatable framework, two fully worked scenarios, and a mock interview.

---

## The framework: a 7-step script for any RAG design question

Say these steps out loud — interviewers grade *structure* as much as content.

### 1. Clarify requirements (don't skip — they're testing this)
Ask about:
- **Corpus**: how many docs, what types (PDF/HTML/tables/code), how often they change, languages.
- **Users & scale**: concurrent users, QPS, peak vs average.
- **Quality bar**: accuracy needs, must it cite sources, must it refuse when unsure.
- **NFRs**: latency target (TTFT/p90), cost ceiling, uptime SLA.
- **Security/compliance**: multi-tenant? PII? data residency? access control?
Restate the requirements before designing.

### 2. Sketch the high-level architecture
Draw the two pipelines: **indexing** (load → clean → chunk → embed → upsert) and **query** (auth → guardrail → route → retrieve → rerank → generate → guardrail → respond), plus vector DB, cache, and observability. (See `docs/11`.)

### 3. Decide the indexing strategy
Loaders per source; cleaning; **chunking** (recursive ~512/overlap, structure-aware where possible); embedding model; vector DB choice; metadata schema (source, page, tenant, date, permissions); freshness mechanism (event-driven, idempotent upserts, deletes).

### 4. Decide the retrieval strategy
**Hybrid** (vector + BM25 + RRF) + **reranking**; top-k (retrieve ~20 → rerank ~4); metadata filters (incl. per-tenant access control); query transforms (multi-query/HyDE) only if eval justifies them.

### 5. Decide the generation strategy
Grounded prompt + citations + refusal; temperature 0; model tiering (small default, escalate); streaming; output guardrail/faithfulness check.

### 6. Address the NFRs explicitly with numbers
Latency (cache + rerank-to-few + stream → TTFT p90 < 2s), scale (stateless autoscaled service; size the vector DB), cost (token control via routing/caching/tight retrieval), reliability (retries, graceful degradation), security (untrusted-context handling, access filters, PII), compliance (residency, right-to-be-forgotten).

### 7. Evaluation & operations
Golden-set offline eval in CI; online eval with drift alerts; full tracing; metrics dashboards; feedback loop. State how you'd detect and roll back a regression.

> Throughout: **name the trade-off** for each choice. "I'd use pgvector because we're already on Postgres and at this scale a dedicated DB isn't worth the ops" beats "I'd use Pinecone because it's popular."

---

## Worked scenario A — Internal documentation assistant

**Prompt:** *"Design a RAG assistant over 10,000 internal documents that change constantly, serving 1,000 concurrent users with cited answers and <2s p90 latency."*

**1. Clarify:** doc types (wiki + PDFs + tickets), update rate (hundreds/day), must cite sources, must respect per-team access permissions, internal-only.

**2. Architecture:** separated indexing + query pipelines; Qdrant (self-hosted, strong hybrid + filtering); semantic cache; tracing via Langfuse.

**3. Indexing:** source-specific loaders; recursive chunking ~512/64 (structure-aware for Markdown); `text-embedding-3-small`; metadata = {source, url, team, updated_at, acl}; **event-driven** re-index on doc change with idempotent upserts + deletes; freshness SLA ~5 min.

**4. Retrieval:** hybrid (vector + BM25) → RRF → cross-encoder rerank to 4; **pre-filter by user's team ACL** (security); top-k retrieve 20.

**5. Generation:** grounded, cited prompt with refusal; `gpt-4o-mini` default, escalate to `gpt-4o` for flagged-hard queries; stream tokens.

**6. NFRs:** <2s p90 via semantic cache (high hit rate on repeated internal questions), rerank-to-few, streaming, warm vector DB; 1,000 concurrent users via horizontally-scaled stateless query service behind a load balancer; cost controlled by caching + mini model + tight top-k; 99.9% uptime via retries + degrade-to-cache.

**7. Eval/ops:** golden set per team in CI; online eval sampling; trace every request (chunk IDs, scores, prompt, tokens, latency); thumbs feedback grows the golden set; access-control tests in CI.

**Likely follow-ups:** "How do you stop a user seeing another team's docs?" (ACL pre-filter on every query, tested in CI). "A doc was updated but answers are stale." (check freshness pipeline + cache invalidation). "Latency spiked." (trace per-stage timings; is it retrieval, rerank, or generation? is the cache cold? did a re-index saturate the DB?).

---

## Worked scenario B — Customer-facing support bot

**Prompt:** *"Design a public support chatbot over product docs + past tickets. Must be cheap, must not hallucinate, must escalate to a human when unsure."*

**Key differences from A:** untrusted *public* input (injection/abuse), tighter cost, explicit refusal/escalation, and brand-safety.

**Highlights:**
- **Guardrails** on input (prompt-injection, abuse, PII) and output (faithfulness check, toxicity); treat retrieved tickets as untrusted (they may contain injected text).
- **Adaptive routing**: chit-chat → canned/no-retrieval; FAQ → simple RAG; complex → multi-step; out-of-scope/low-confidence → **escalate to human**.
- **Refusal/escalation** when top rerank score < threshold or faithfulness check fails — never guess to a customer.
- **Cost**: aggressive semantic caching (support questions repeat a lot), mini model, tight top-k.
- **Eval**: golden set from real tickets; track refusal rate and escalation precision; online eval for drift after doc updates.

**Likely follow-ups:** "How do you prevent a malicious user extracting your system prompt or other customers' data?" (untrusted-context handling + access filters + injection guardrails). "How do you measure 'doesn't hallucinate'?" (faithfulness metric + output guardrail + human review on a sample).

---

## Mock interview (do this on Day 14 — answer out loud, then check yourself)

1. Design a RAG system for a law firm to query 2M case documents with citations. What's different about *legal*? (precision, exact citation, access control, domain embeddings, refusal, audit trail)
2. Your RAG answers are correct but slow (p90 = 6s). Walk me through diagnosing and fixing it.
3. Faithfulness dropped from 0.92 to 0.78 after a "small" prompt change shipped. What happened and how do you prevent it next time?
4. The corpus grew from 10k to 10M documents. What breaks and what do you change?
5. Build vs buy for a 5-person startup vs a 5,000-person enterprise — argue both.
6. A stakeholder demands "100% accuracy." Respond.
7. How would you add multi-language support to an existing English RAG system?
8. Walk me through how a single document update propagates to a correct, fresh answer.

**Self-scoring rubric (per answer):**
- [ ] Clarified requirements before designing.
- [ ] Covered both indexing and query pipelines.
- [ ] Named a metric for the relevant component.
- [ ] Stated at least one explicit trade-off with a reason.
- [ ] Addressed an NFR with a number.
- [ ] Mentioned how you'd evaluate/monitor it.

If you hit 5–6 of those consistently, you're interviewing at architect level.

---

## Phrases that signal seniority

- "Before I design, let me clarify the requirements…"
- "I'd separate indexing from querying so re-indexing never spikes query latency."
- "I'd default to X, but the trade-off is Y; if requirement Z changes I'd switch to W."
- "I'd validate that with the golden set / online eval — I wouldn't ship it unmeasured."
- "The dominant cost here is tokens, so I'd control it with caching, routing, and tight retrieval."
- "I'd treat retrieved content as untrusted to resist prompt injection."
