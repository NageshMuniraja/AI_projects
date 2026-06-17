# Project 06 — Agentic RAG (routing + multi-step + tools)

**Level:** Advanced · **Days:** 9–10 · **Read first:** `docs/09_agentic_rag.md`

Retrieval stops being a straight line and becomes a **decision loop**. Built from scratch so you can see every decision (no framework hiding the mechanics). It demonstrates the two highest-ROI agentic patterns:

1. **Adaptive routing** — classify each query and send it down the cheapest path that works.
2. **Multi-step retrieval** — decompose a complex query, retrieve per sub-question, synthesize.

Plus a **calculator tool** and a **max-step budget** so the loop can't run away.

## Run it

```bash
cd projects/06_agentic_rag
python agentic_rag.py
python agentic_rag.py "hi there"                                  # → no_retrieval
python agentic_rag.py "How long is the free trial?"               # → simple
python agentic_rag.py "what is 499 * 12 for annual Premium?"      # → tool
python agentic_rag.py "Compare Standard vs Premium support cost and response time"  # → multi_hop
```

It prints the **route chosen** and, for multi-hop, each sub-question and its sub-answer before the synthesis. Watching the route is the point.

## The four routes

- **no_retrieval** — greetings/chit-chat answer directly, skipping the vector DB (saves latency + cost).
- **tool** — arithmetic goes to a sandboxed calculator (LLMs are bad at math).
- **simple** — one lookup + grounded answer (classic RAG).
- **multi_hop** — decompose → retrieve per sub-question → synthesize.

## Why this matters (interview-grade points)

- **Adaptive routing matches pipeline cost to query difficulty** — the cheap path handles easy/out-of-scope queries; the expensive multi-step path only fires when needed. This is the #1 cost-control pattern in 2026 production RAG.
- **Multi-hop retrieval answers questions single-shot vector search can't** — each step's result informs the next query.
- **Guardrails on the loop:** `MAX_STEPS` caps work; the calculator input is sanitized (no arbitrary `eval`). Non-termination and runaway cost are the classic agent failures (Doc 09).

## Stretch goals

1. **Add a self-grading step (CRAG).** After retrieval, ask the LLM "is this context relevant?"; if not, rewrite the query and retrieve again (cap retries).
2. **Add a tool.** A fake "web_search" or "sql_lookup" tool, and teach the router when to pick it.
3. **Trace + cost.** Log every LLM call, its tokens, and latency; print total cost per query and compare routes.
4. **Port to LangGraph.** Re-implement the router + loop as a LangGraph state machine (nodes = states, edges = transitions) — the production-friendly way to make loops explicit and debuggable.
5. **Eval the agent.** Run the multi-hop path through Project 05's harness and confirm it beats `simple` on genuinely multi-hop questions (and that it does *not* waste cost on easy ones).

## Concepts made concrete

- Adaptive RAG / query routing, query decomposition, tool use (Doc 09)
- The ReAct-style retrieve→reason→retrieve loop
- Loop guardrails: max-step budget, sanitized tools, graceful synthesis

## Common issues

- Router picks the "wrong" route → it's an LLM classifier; tighten `ROUTE_SYSTEM` wording or add few-shot examples. Misroutes are a real production concern worth experiencing.
- Multi-hop is slow/pricey → that's the lesson; it's why routing exists. Keep `MAX_STEPS` small.
