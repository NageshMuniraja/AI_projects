# 09 · Agentic RAG

> Days 9–10. Give the retrieval system the ability to *reason about* and *act on* its own retrieval.

## From pipeline to agent

Classic RAG is a **fixed pipeline**: retrieve once, generate once. **Agentic RAG** lets an LLM *decide* what to do: whether to retrieve, what to search for, whether the results are good enough, whether to search again, which tool to call, and when it's done.

The shift: retrieval becomes a **loop with decisions**, not a straight line.

```
classic:   query ─► retrieve ─► generate ─► answer
agentic:   query ─► [decide ─► act (retrieve / tool / rewrite) ─► observe ─► reflect]✲ ─► answer
                     ↑__________________ loop until confident or budget hit __________________|
```

## The building blocks

### 1. Routing (Adaptive RAG) — build this first (Day 9)
A classifier (an LLM or a small model) labels each query and routes it:
- **No retrieval** → chit-chat, greetings → answer directly, skip the vector DB (saves cost + latency).
- **Simple lookup** → single retrieval + generate (the classic path).
- **Multi-hop / complex** → decomposition or the full agent loop.
- **Out-of-scope** → refuse or hand off.

This alone — matching pipeline cost to query difficulty — is the highest-ROI agentic feature and the 2026 production default.

### 2. Query decomposition & multi-step retrieval (Day 10)
For "Which of our 2026 products has the longest warranty, and what does it cover?" the agent:
1. retrieves the list of 2026 products,
2. for each, retrieves the warranty length,
3. compares, picks the longest,
4. retrieves that warranty's coverage,
5. synthesizes.

Each step's result *informs the next query*. This **iterative retrieve→reason→retrieve** is what vector-search-once can't do.

### 3. Tool use
The agent can call tools beyond the vector DB:
- a **calculator** (LLMs are bad at arithmetic),
- **SQL / API** lookups for structured/live data,
- **web search** for fresh info not in the corpus,
- another **RAG index** (multi-source routing).

RAG becomes one tool among several the agent orchestrates.

### 4. Self-reflection / correction (CRAG-style)
After retrieving or drafting, the agent **grades its own work**: "Is this context relevant? Is my answer supported?" If not, it rewrites the query, retrieves again, or escalates. This catches the "answered confidently from junk context" failure.

## The standard agent loop (ReAct)

**ReAct = Reason + Act.** Each turn the LLM emits a thought, an action (tool + input), and reads the observation, repeating until it produces a final answer:

```
Thought: I need the 2026 product list.
Action: retrieve("2026 product lineup")
Observation: [chunks...]
Thought: Now I need each product's warranty length.
Action: retrieve("warranty length product X")
...
Thought: I have enough. Longest is X at 5 years, covering ...
Final Answer: ... [citations]
```

You'll implement a routed, looped version in `projects/06_agentic_rag`, using **LangGraph** (a graph of nodes/edges = states/transitions) because it makes the loop, the branches, and the stop conditions explicit and debuggable.

## The hard parts (this is what interviews probe)

- **Latency & cost explode.** Each loop step is one or more LLM calls. A 5-step agent can be 10× the cost/latency of classic RAG. → Use routing so only hard queries pay this.
- **Infinite loops / non-termination.** → Always set a **max-steps budget** and a fallback ("I couldn't fully resolve this; here's what I found").
- **Error compounding.** A wrong step 2 poisons steps 3–5. → Reflection/grading + the ability to backtrack.
- **Determinism & testability.** Agents are harder to evaluate than pipelines. → Log every step (trace), eval end-to-end, and pin temperature 0 for the controller.
- **When NOT to use an agent.** If a single retrieval answers 95% of queries, a full agent is over-engineering. Start simple; add agentic behavior where the data shows you need it.

## Frameworks (2026)

- **LangGraph** (LangChain): explicit state-machine graphs; great for controllable loops, routing, human-in-the-loop. Used in `06_agentic_rag`.
- **LlamaIndex agents / workflows**: strong when retrieval is the core and you want query engines as tools.
- **DSPy**: programmatic prompt/pipeline optimization rather than hand-written prompts.
- Roll-your-own: a `while` loop calling `chat()` with tool-call parsing is enough to understand the mechanics — and you'll see exactly that before reaching for a framework.

## Design checklist for an agentic RAG

- [ ] Is there a cheap path for easy/out-of-scope queries (routing)?
- [ ] Is there a max-step budget and a graceful fallback?
- [ ] Does each step's output get graded/validated?
- [ ] Are all steps traced for debugging and eval?
- [ ] Have you confirmed (with eval) that the agent beats classic RAG enough to justify the cost?

## Interview soundbites

- "Agentic RAG turns retrieval into a decision loop: route, decompose, retrieve iteratively, call tools, and self-correct."
- "Adaptive routing is the highest-ROI piece — full agent only for queries that need it, cheap path for the rest."
- "The risks are latency, cost, and non-termination; I cap steps, add fallbacks, grade each step, and trace everything."
- "I don't reach for an agent until single-shot retrieval provably can't answer the query class."

➡️ Next: `docs/10_graph_rag.md`.
