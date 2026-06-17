# Project 07 — Graph RAG (multi-hop reasoning)

**Level:** Advanced · **Day:** 11 · **Read first:** `docs/10_graph_rag.md`

Some questions aren't about *similarity*, they're about *connections*: "Who reports to the person who owns the billing service?" Pure vector search finds similar sentences but can't reliably **chain** facts. Here you build a small **knowledge graph** and answer multi-hop questions by **traversing** it — then compare side-by-side with vector RAG.

## Run it

```bash
cd projects/07_graph_rag
python graph_rag.py
python graph_rag.py --show-graph                                   # print the extracted graph
python graph_rag.py "Who reports to the person who owns the billing service?"
```

For each question it prints the **Graph RAG** answer and the **Vector RAG** answer so you can see the difference.

## How it works (all in `graph_rag.py`)

1. **Extract** — an LLM turns the document into `subject | relation | object` triples (`reports_to`, `owns`, `depends_on`…).
2. **Build** — triples become a directed graph (NetworkX).
3. **Retrieve** — find entities mentioned in the question, gather their N-hop neighborhood as readable `A --relation--> B` facts.
4. **Answer** — the LLM reasons over those connected facts; vector RAG answers the same question from top-k similar sentences for contrast.

## What to observe

The data is written so the facts are **spread across separate sentences**:
- "The Sol control plane handles billing… owned by **Lena Ortiz**."
- "**Sam Cole** and **Dana Kim** report to **Lena Ortiz**."

Vector RAG retrieves *similar* sentences but often can't connect billing → Sol → Lena → her reports. Graph traversal follows the edges and lands on **Sam Cole and Dana Kim**. That's the multi-hop win.

## When to actually use Graph RAG (interview point)

Use it for **relational, multi-hop, or global** questions (org charts, dependency maps, supply chains). **Don't** use it when a single passage answers the question — it's more expensive to build and maintain (extraction quality, entity resolution, freshness). In practice it's usually **hybridized** with vector search.

## Stretch goals

1. **Break vector RAG on purpose.** Write a 3-hop question and confirm only the graph gets it right.
2. **Entity resolution.** Add "Lena" and "Ms. Ortiz" as variants and merge them to the same node.
3. **Hybrid.** Combine graph facts + vector chunks into one context and see if it beats either alone.
4. **Global summary (GraphRAG).** Detect communities (`networkx.community`) and have the LLM summarize each; answer a "what are the main teams and what do they own?" question from summaries.
5. **Persist to Neo4j.** Swap the in-memory graph for Neo4j and query with Cypher — the production path.

## Concepts made concrete

- Triple extraction, knowledge graphs, multi-hop traversal (Doc 10)
- Why similarity ≠ connection, and when graph beats vectors
- The graph-vs-vector trade-off you must be able to defend

## Common issues

- Extraction varies run-to-run (it's an LLM) → use `--show-graph` to inspect; tighten `EXTRACT_SYSTEM` or pin temperature 0 (already default).
- Entity not found → the matcher is simple on purpose; improve `find_entities` (a great stretch goal).
