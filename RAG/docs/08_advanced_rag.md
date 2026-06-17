# 08 · Advanced RAG Techniques

> Day 8. A toolbox of upgrades. Rule: add a technique only if the eval harness (Doc 07) shows it earns its latency/cost.

The naive pipeline (embed query → search → stuff → answer) fails in predictable ways. Each technique below fixes a specific failure. Learn them as *failure → fix* pairs.

## Query-side techniques (improve the question before retrieval)

### Multi-query expansion
**Failure:** one phrasing misses relevantly-worded chunks.
**Fix:** ask an LLM to rewrite the query into 3–5 variations, retrieve for each, and union/RRF the results. Catches synonyms and alternate framings. Cost: +1 LLM call + more searches.

### HyDE (Hypothetical Document Embeddings)
**Failure:** a short question embeds far from long, detailed answer passages (asymmetry).
**Fix:** have the LLM write a *hypothetical answer* to the question, embed *that*, and search with it. The fake answer is shaped like real documents, so it retrieves better. Surprisingly effective for sparse/technical corpora. Cost: +1 LLM call; can hurt if the hallucinated answer drifts.

### Query decomposition
**Failure:** multi-part questions ("compare A's 2024 and 2025 refund policies") need several distinct retrievals.
**Fix:** break the query into sub-questions, retrieve + answer each, then synthesize. Foundational to agentic RAG (Doc 09).

### Query routing / classification
**Failure:** you run the full heavy pipeline even for trivial or out-of-scope queries.
**Fix:** classify the query (simple lookup / multi-hop / chit-chat / needs-a-tool) and route to the cheapest pipeline that can handle it. This is **Adaptive RAG**, the 2026 default for cost control. You build it in `projects/06_agentic_rag`.

## Index/retrieval-side techniques (change what's stored or returned)

### Parent-document / small-to-big retrieval
**Failure:** small chunks match precisely but are too fragmentary for the LLM to reason over; big chunks read well but match poorly.
**Fix:** embed **small** child chunks for matching, but when one hits, return its **larger parent** chunk to the LLM. Precision of small + context of big.

### Contextual retrieval
**Failure:** a chunk like "the limit is 30 days" is meaningless out of context (30 days of *what*?).
**Fix:** at index time, prepend an LLM-generated one-liner situating the chunk ("From the 2026 refund policy: the return window…") *before* embedding. Big recall gains; costs an LLM call per chunk at ingestion (cache it).

### Sentence-window retrieval
Embed single sentences for precise matching, but return a *window* of surrounding sentences for context. A lightweight cousin of small-to-big.

### Metadata & self-query
Let an LLM translate "refunds after 2025" into a **metadata filter** (`date > 2025`) plus a semantic query. Combines structured filtering with semantic search.

## Post-retrieval techniques (clean up before generation)

### Reranking (recap from Doc 05)
Cross-encoder re-scores candidates; keep the top few. Almost always worth it.

### Contextual compression
**Failure:** retrieved chunks contain relevant sentences buried in irrelevant ones, wasting the context window.
**Fix:** an LLM (or a smaller extractor) strips each chunk down to only the sentences relevant to the query before they go in the prompt. Less noise, lower cost, fights "lost in the middle."

### Corrective RAG (CRAG) / self-reflection
**Failure:** retrieval returned weak/irrelevant context but the model answers anyway.
**Fix:** grade the retrieved context; if it's poor, take corrective action — re-retrieve with a rewritten query, fall back to a web/tool search, or refuse. Bridges into agentic RAG.

## How they compose (a strong advanced pipeline)

```
query
 └─ route (adaptive) ─ if retrieval needed:
       ├─ multi-query / HyDE  ─► better queries
       ├─ hybrid search (BM25 + vector) ─► top 20
       ├─ rerank (cross-encoder) ─► top 6
       ├─ contextual compression ─► trimmed context
       └─ generate (grounded, cited)
              └─ self-grade; if unfaithful → re-retrieve or refuse
```

You don't need all of it. On Day 8 you'll add multi-query, HyDE, and compression to `04_hybrid_search`, then **measure** which ones actually help your corpus — and drop the rest.

## The discipline that makes you senior

Every technique here costs latency, money, or complexity. The amateur adds all of them; the architect adds the *one or two* that move the eval numbers for *this* use case and can explain why. "We added HyDE because our queries are short and our docs are dense, and it lifted context recall from 0.71 to 0.83 for +120ms — worth it" is an architect sentence.

## Interview soundbites

- "I think in failure→fix pairs: HyDE for query/doc asymmetry, multi-query for phrasing gaps, small-to-big for the precision/context trade-off, compression for noisy chunks, CRAG for bad retrieval."
- "Adaptive routing matches pipeline complexity to query complexity — full arsenal only when the query needs it, cheap path otherwise."
- "I justify every advanced technique with an eval delta and a latency/cost number, and I drop the ones that don't pay."

➡️ Next: `docs/09_agentic_rag.md`.
