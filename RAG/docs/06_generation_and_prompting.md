# 06 · Generation & Prompting

> Day 6. You have great context. Now make the LLM use it faithfully, cite it, and refuse when it can't.

## The job of the generation step

Take the retrieved chunks + the question and produce an answer that is:
1. **Grounded** — every claim supported by the supplied context.
2. **Cited** — points to which chunk/source each claim came from.
3. **Honest** — says "I don't know" / "not in the provided documents" when the context lacks the answer.
4. **On-format** — the length, tone, and structure the app needs.

Prompting is how you enforce all four.

## A solid grounded-RAG prompt template

```text
SYSTEM:
You are a precise assistant. Answer the user's question using ONLY the context below.
Rules:
- If the answer is not in the context, say: "I don't have enough information in the provided documents to answer that." Do not use outside knowledge.
- Cite the source of each claim using its [number].
- Be concise. Do not speculate.

CONTEXT:
[1] (refund_policy.pdf, p.4) <chunk text>
[2] (faq.md, "Returns") <chunk text>
[3] ...

QUESTION:
{user question}

ANSWER (with [n] citations):
```

Why each rule exists:
- **"ONLY the context"** + **"don't use outside knowledge"** → cuts hallucination and stops the model leaking stale training facts.
- **Explicit refusal sentence** → gives the model a safe exit instead of inventing. Models hallucinate most when they feel forced to answer.
- **Numbered citations** → provenance + auditability; you can trace any sentence to a chunk.
- **temperature = 0** → deterministic, factual. RAG is not the place for creativity.

## Context assembly (the part people get wrong)

How you *arrange* the chunks matters as much as which chunks:
- **Rerank first**, then include only the top few. More context ≠ better (noise + cost + "lost in the middle", Doc 05).
- **Order by relevance**, best chunk first. Consider placing a critical chunk both first and last for long contexts.
- **Label each chunk** with an index and source so the model can cite it and you can render the citation.
- **Budget tokens**: leave room for the question + answer. Track token counts (use `tiktoken`).
- **De-duplicate** near-identical chunks (MMR) so you don't waste the window.

## Reducing hallucination (a layered defense)

No single trick is enough; stack them:
1. **Retrieval first.** If the right chunk isn't retrieved, prompting can't save you. Fix retrieval before blaming the prompt.
2. **Grounding instructions** + an explicit refusal path (above).
3. **A relevance gate**: if the top reranker score is below a threshold, skip generation and return the refusal. Don't answer from weak context. (`02_pdf_qa` stretch goal.)
4. **Citation enforcement**: require `[n]` markers; optionally post-check that cited chunks exist.
5. **Faithfulness eval** (Doc 07): score how much of the answer is actually supported by context, and catch regressions.
6. **(Advanced)** self-check / "grader" pass: a second LLM call verifies the answer is supported before returning it (Corrective RAG, Doc 08/09).

## Prompting patterns worth knowing

- **Few-shot**: include 1–3 examples of a good grounded, cited answer to lock in format.
- **Structured output**: ask for JSON (`{"answer":..., "citations":[...], "confidence":...}`) when a downstream system consumes it. Use the provider's JSON/structured-output mode.
- **"Quote then answer"**: ask the model to first extract the exact supporting sentences, then answer. Improves faithfulness and gives you evidence.
- **Refusal calibration**: test with out-of-scope questions; tune until it refuses gracefully instead of guessing.

## Streaming, latency, and cost

- **Stream** tokens to the user so perceived latency drops (you'll do this in `08_production_rag`).
- **Model tiering**: use a small model (`gpt-4o-mini`) for easy questions, escalate to a larger one only when needed (ties into adaptive routing, Doc 09).
- **Token discipline**: the prompt (context) usually dominates input cost. Tighter retrieval = cheaper *and* better.

## A reusable generation function (shape you'll build)

```python
SYSTEM = "...grounded RAG rules from above..."

def generate(question, reranked_chunks, min_score=0.2):
    if not reranked_chunks or reranked_chunks[0].score < min_score:
        return "I don't have enough information in the provided documents to answer that.", []
    context = "\n".join(f"[{i+1}] ({c.source}) {c.text}" for i, c in enumerate(reranked_chunks))
    user = f"CONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nANSWER (with [n] citations):"
    return chat(SYSTEM, user, temperature=0.0), reranked_chunks
```

You harden `02_pdf_qa` into roughly this on Day 6.

## Interview soundbites

- "Generation should be grounded, cited, and able to refuse; I enforce that with a strict system prompt, temperature 0, and a relevance gate."
- "More context isn't better — rerank to a few high-precision chunks and order by relevance to beat 'lost in the middle'."
- "Hallucination is layered defense: fix retrieval, ground the prompt, gate on score, enforce citations, then measure faithfulness."

➡️ Next: `docs/07_evaluation_ragas.md` — how you turn opinions into numbers.
