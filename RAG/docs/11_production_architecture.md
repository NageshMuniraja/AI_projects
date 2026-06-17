# 11 · Production Architecture

> Days 12–13. This chapter is the difference between a notebook demo and a system 1,000 people depend on. It's also where architect interviews live.

## The first principle: split indexing from querying

In production these are **two independent pipelines** with different scaling, schedules, and owners:

```
INDEXING PIPELINE (offline / event-driven)        QUERY PIPELINE (online / per request)
─────────────────────────────────────────        ──────────────────────────────────────
source change ─► load ─► clean ─► chunk            request ─► auth ─► (cache?) ─► retrieve
  ─► embed ─► upsert to vector DB (+metadata)         ─► rerank ─► assemble ─► generate (stream)
  ─► delete stale ─► (re)build graph                  ─► guardrails ─► log/trace ─► respond
runs on: cron / file events / queue                run on: API server, autoscaled
```

Why separate? Indexing is bursty and heavy; querying must be low-latency and always-on. Coupling them means a re-index spikes your query latency. Keep them apart.

## Reference architecture

```
                ┌──────────── INGESTION ────────────┐
 data sources ─►│ loaders → cleaners → chunker →      │
 (S3, DBs,      │ embedder → vector DB upsert         │──► Vector DB (+ optional Graph DB)
  wikis, APIs)  │ (queue + workers, idempotent IDs)   │           ▲
                └─────────────────────────────────────┘           │ retrieve / filter
                                                                   │
 user ─► API gateway ─► RAG service ─────────────────────────────►┤
          (authn/z,     (FastAPI):                                 │
           rate limit)   route → cache → retrieve → rerank →       │
                         compress → generate(LLM) → guardrails ────┘
                              │            │
                          Semantic       LLM provider
                            cache         (OpenAI/Anthropic)
                              │
                         Observability: logs + traces + metrics + online eval
```

You build a real (smaller) version of the online half in `projects/08_production_rag`.

## Non-functional requirements (NFRs) — what architects actually get graded on

An architect doesn't just make it work; they make it meet **latency, scale, cost, reliability, security, and compliance** targets. For any design, state numbers:

### Latency
- Track **TTFT (time-to-first-token)** and **end-to-end p50/p90/p99**, not averages.
- A common bar: **TTFT p90 < 2s**; breach it and you autoscale or shed load.
- Levers: **stream** tokens (huge perceived-latency win), rerank to fewer chunks, cache, smaller/faster models for easy queries, run retrieval steps concurrently, keep the vector DB warm.

### Scale & throughput
- Stateless query service behind a load balancer → horizontal autoscaling.
- Vector DB sized for corpus + QPS (HNSW memory!).
- Batch + queue the indexing pipeline; backpressure so ingestion can't drown queries.

### Cost
- Dominant cost is **LLM tokens**. Control with: tight retrieval (fewer/shorter chunks), model tiering (mini by default), **semantic caching**, and routing so trivial queries don't trigger agents.
- Embeddings are cheap and cacheable; storage scales with vector count × dimension.
- Track cost per query; alert on spikes (a runaway agent loop can 50× a query).

### Reliability
- 99.9% uptime → redundancy, retries with backoff on the LLM/embedding APIs, timeouts, circuit breakers, graceful degradation (e.g., serve from cache or return top chunks without generation if the LLM is down).

### Security & privacy
- **Per-tenant / per-user access control** via metadata filters — never retrieve a chunk the user can't see (the classic RAG data-leak).
- **PII handling**: redact at ingestion or generation as required.
- **Prompt-injection defense**: untrusted documents can contain "ignore your instructions" — treat retrieved text as data, not commands; sanitize; use guardrail checks.
- Secrets management, encryption at rest/in transit, audit logs.

### Compliance
- Data residency, retention, the **right to be forgotten** (you must be able to delete a user's docs *and* their chunks/embeddings), and citeable provenance.

## Caching (a top latency + cost win)

- **Exact cache**: same query string → stored answer.
- **Semantic cache**: embed the query; if a *previous* query is within a similarity threshold, return its answer. Catches paraphrases. (You add this in `08_production_rag`.)
- **Component caches**: cache embeddings (always) and reranker scores.
- Watch **staleness**: invalidate caches when underlying docs change.

## Observability (you can't operate what you can't see)

- **Tracing**: capture every stage per request — query, retrieved chunk IDs + scores, reranked set, final prompt, model, tokens, latency per stage, cost. This is how you debug "why did it say that?". Tools: LangSmith, Langfuse, Phoenix/Arize, OpenTelemetry.
- **Metrics**: latency percentiles, QPS, cache hit rate, retrieval score distributions, refusal rate, cost/query, error rate.
- **Online evaluation**: sample real traffic, score with RAGAS/LLM-judge on a schedule, alert on drift. Offline tests go stale; production truth doesn't.
- **Feedback loop**: capture thumbs up/down and use it to grow the golden set and find weak spots.

## Guardrails (input and output)

- **Input**: prompt-injection / jailbreak detection, off-topic/abuse filtering, PII detection.
- **Output**: faithfulness/grounding check before returning, citation validation, toxicity/PII leak check, refusal when context is weak (relevance gate, Doc 06).

## Freshness & re-indexing

- **Trigger**: file/event-driven (webhook on doc change) or scheduled.
- **Idempotent upserts** with stable chunk IDs; **delete** stale chunks (don't just add).
- **Incremental** > full re-index when possible.
- Decide your **freshness SLA** ("new docs searchable within 5 min") and design ingestion to meet it.

## Evaluation in CI/CD

Wire the eval harness (Doc 07) into your pipeline: a PR that changes the prompt, chunker, or model runs the golden set and **fails the build** if faithfulness/precision/recall regress past a threshold. This is what stops "small tweaks" from quietly breaking quality.

## Build vs buy (a real architect decision)

- **Build** (LangChain/LlamaIndex + Qdrant/pgvector + your code): control, cost at scale, customizability; you own ops and eval.
- **Buy** (Vectara, Ragie, managed RAG): fast to launch, less ops, but less control and per-query cost; data governance questions.
- Decision factors: data sensitivity, scale, team size, time-to-market, and how custom your retrieval needs are. Be ready to justify it.

## Interview soundbites

- "I separate indexing and query pipelines so re-indexing never spikes query latency."
- "I design to NFRs with numbers: TTFT p90 < 2s, 99.9% uptime, cost/query budget, per-tenant access control."
- "Biggest cost is tokens; I control it with tight retrieval, model tiering, semantic caching, and adaptive routing."
- "Full tracing per request + online eval is non-negotiable — it's how I debug and prevent drift."
- "Access control via metadata filters prevents the classic RAG data leak; I treat retrieved text as untrusted to resist prompt injection."

➡️ Last doc: `docs/12_glossary.md`. Then it's interview prep.
