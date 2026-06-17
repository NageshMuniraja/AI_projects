# 10 · Graph RAG

> Day 11. When relationships matter more than similarity.

## The failure that motivates Graph RAG

Vector RAG retrieves chunks that are *semantically similar* to the query. But some questions aren't about similarity — they're about **connections**:

- "Who reports to the manager who owns the billing service?"
- "What downstream services break if database X goes down?"
- "Summarize how these 12 incident reports relate to each other."

These are **multi-hop** (the answer requires chaining facts A→B→C) or **global** (you need to understand the whole corpus, not a few chunks). Vector search struggles: the relevant chunks may not be textually similar to the query *or to each other*, and stuffing the top-k misses the connective tissue.

## The idea

Build a **knowledge graph** from your documents:
- **Nodes** = entities (people, services, products, concepts).
- **Edges** = relationships ("reports_to", "depends_on", "refunds", "authored_by").

Then **retrieve by traversing the graph**, optionally blended with vector search.

```
documents ─► extract (entities + relationships) ─► knowledge graph
query ─► find entry-point nodes (vector/keyword) ─► traverse edges (multi-hop) ─► assemble connected context ─► generate
```

## How the graph gets built

1. **Entity & relation extraction**: an LLM reads each chunk and emits triples — `(subject, relation, object)`, e.g. `(Alice, reports_to, Bob)`, `(BillingService, depends_on, Postgres)`. This is the costly, quality-critical step.
2. **Graph construction**: load triples into a graph store (Neo4j in production; **NetworkX** in-memory for `07_graph_rag`). De-duplicate/merge entities ("DB" = "database X").
3. **(GraphRAG) Community detection + summaries**: cluster the graph into communities and have an LLM write a summary per community. This is what powers **global** questions ("what are the main themes?") — you answer from community summaries instead of raw chunks. (This is the approach popularized by Microsoft's GraphRAG.)

## How retrieval works

- **Local (multi-hop) queries**: find the entities mentioned in the query (entry points), then walk edges N hops out to gather the connected subgraph, and feed that as context. This answers "who reports to the person who owns X" by literally following `owns` then `reports_to`.
- **Global queries**: route over **community summaries** to synthesize a corpus-wide answer.
- **Hybrid (the practical default)**: combine graph traversal with vector search — vectors find semantically relevant chunks, the graph adds the connected/structural context. You get *similar* and *related*.

## When to use it (and when not to)

**Use Graph RAG when:**
- Your domain is rich in **entities and relationships** (org charts, supply chains, dependency maps, medical/legal knowledge, fraud rings).
- Questions are **multi-hop** or **global/summarizing**.
- You need to reason over **structure**, not just find passages.

**Don't bother when:**
- Questions are answered by a single relevant passage (most FAQ/support/doc-search).
- Your data isn't very relational.
- You can't afford the extraction cost or graph maintenance.

Graph RAG is **more expensive and complex** to build and maintain (extraction quality, entity resolution, keeping the graph fresh). It's a targeted tool, not a default upgrade.

## What you'll build (`projects/07_graph_rag`)

A small, dependency-light Graph RAG with **NetworkX**:
1. LLM extracts `(subject, relation, object)` triples from a small corpus (e.g., a fictional company's org + services).
2. Build an in-memory graph.
3. Answer a **multi-hop** question by locating entry nodes and traversing edges.
4. Compare against vector RAG on the same question to *see* graph win where vectors can't.

This makes the concept concrete without standing up Neo4j.

## Production notes

- **Graph store**: Neo4j (Cypher queries), or graph features in some vector DBs; Postgres can do simple graphs too.
- **Freshness**: re-extraction on document change; entity resolution gets harder as the graph grows.
- **Hybrid serving**: most real "GraphRAG" systems are graph **plus** vector, with a router deciding which to lean on per query (ties back to Doc 09).

## Interview soundbites

- "Graph RAG answers multi-hop and global questions by traversing entity-relationship structure, where pure vector similarity falls short."
- "Build it by LLM-extracting triples into a graph; for global questions, summarize graph communities and answer from those."
- "It's costlier to build and maintain (extraction, entity resolution, freshness), so I use it only for relational, multi-hop domains — usually hybridized with vector search."

➡️ Next: `docs/11_production_architecture.md`.
