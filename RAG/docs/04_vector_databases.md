# 04 · Vector Databases

> Day 4. Where your embeddings live and how they're searched fast.

## What a vector DB does

It stores millions of vectors and, given a query vector, returns the most similar ones in milliseconds. Doing this by brute force (compare the query to every vector) is O(N) and too slow at scale, so vector DBs use **Approximate Nearest Neighbor (ANN)** indexes that trade a tiny bit of accuracy for enormous speed.

A vector DB stores three things per record:
1. the **vector** (for similarity search),
2. the original **text/payload** (so you can read it),
3. **metadata** (for filtering and citations).

## ANN index types (the interview favorite)

| Index | Idea | Strength | Trade-off |
|---|---|---|---|
| **Flat / brute force** | compare to everything | exact, simple | slow above ~10k–100k vectors |
| **HNSW** (graph) | navigable small-world graph; hop toward nearest | fast, high recall, great for updates | more memory; the modern default |
| **IVF** (inverted file) | cluster vectors, search only nearby clusters | memory-efficient at huge scale | recall depends on #clusters probed |
| **IVF+PQ / quantization** | compress vectors (product quantization) | massive memory savings | small accuracy loss |

The two dials you'll hear about:
- **HNSW**: `M` (graph connectivity) and `ef_search` (how hard it searches at query time). Higher = better recall, slower.
- **IVF**: `nlist` (clusters) and `nprobe` (clusters searched per query).

**Recall vs latency vs memory is the eternal triangle.** You can't max all three; you choose based on requirements.

## The landscape (2026)

| Option | Type | Use it when |
|---|---|---|
| **Chroma** | embedded / local | Learning, prototypes, small apps. **This repo's default** — no server to run. |
| **pgvector** | Postgres extension | You already use Postgres and want vectors + relational data + filters in one place. |
| **Qdrant** | dedicated, open-source | Production, great hybrid search & filtering, self-host or cloud. |
| **Weaviate** | dedicated, open-source | Production, built-in hybrid + modules. |
| **Milvus** | dedicated, open-source | Very large scale (billions of vectors). |
| **Pinecone** | managed SaaS | You want zero ops and will pay for it. |
| **Vespa** | search engine | Complex ranking + scale; steeper learning curve. |

How to choose, briefly:
- **Prototyping / this course →** Chroma (embedded, persists to disk).
- **Already on Postgres, moderate scale →** pgvector. One database, transactional, easy filtering.
- **Dedicated production, self-hosted →** Qdrant or Weaviate (strong hybrid search).
- **Don't want to run infra →** Pinecone (managed) — trade money for ops.
- **Billions of vectors →** Milvus / Vespa.

> Architect note: the vector DB is rarely the hard part. Retrieval *quality* (chunking, hybrid, reranking) and *operations* (re-indexing, freshness, filtering, cost) matter more than which DB logo you pick. Pick the one that fits your existing stack and ops budget.

## Filtering (don't skip this)

Real apps need **metadata filters**: "search only docs from 2026", "only documents in this user's department", "only this product's manual." Two patterns:
- **Pre-filter**: restrict candidates *before* ANN search (correct results, can be slower).
- **Post-filter**: ANN first, then drop non-matching (faster, but can return too few if filters are strict).

Security tip: filtering on an `allowed_roles` / `tenant_id` field is how you enforce **per-user access control** in multi-tenant RAG. Never retrieve a chunk a user isn't allowed to see.

## Operational realities

- **Re-indexing & freshness**: when a document changes, you must re-chunk, re-embed, and **upsert** (and delete stale chunks). Production systems separate the **indexing pipeline** (runs on data change) from the **query pipeline** (runs per request). (Doc 11.)
- **IDs & idempotency**: give each chunk a stable ID (e.g., `hash(source+offset)`) so re-ingesting doesn't create duplicates.
- **Backups & versioning**: you'll want to roll back a bad index.
- **Cost**: managed DBs price on stored vectors + queries; large dims (3072) cost more to store and search than 1536.

## What you'll do in the projects

- `02_pdf_qa`: use Chroma as a **persistent** store with metadata + citations and metadata filtering.
- `04_hybrid_search`: see why the DB's vector search alone isn't enough and add keyword + reranking on top.
- `08_production_rag`: treat indexing and querying as separate pipelines, add upserts and IDs.

## Interview soundbites

- "HNSW is the modern default index — fast, high recall, handles updates; IVF/PQ wins on memory at massive scale."
- "Recall, latency, and memory form a triangle; you tune `ef_search`/`nprobe` to your SLA."
- "Pick the DB that fits your stack: pgvector if you're on Postgres, Qdrant/Weaviate for dedicated self-hosted, Pinecone to avoid ops."
- "Metadata filtering isn't a nice-to-have — it's how you do citations and per-tenant access control."

➡️ Next: `docs/05_retrieval_strategies.md` — the most important chapter.
