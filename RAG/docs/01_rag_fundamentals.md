# 01 · RAG Fundamentals

> Read this on Day 1, before building `projects/01_hello_rag`.

## What RAG is, in one sentence

**Retrieval-Augmented Generation** = before asking an LLM to answer, you *retrieve* relevant text from your own data and *paste it into the prompt*, so the model answers from facts you supplied instead of only from its training memory.

That's it. Everything else in this repo is making each part of that sentence better, faster, and more trustworthy.

## Why RAG exists (the problem it solves)

A raw LLM has three problems for real applications:

1. **Knowledge cutoff.** It only knows what it saw in training. It can't know your company wiki, last week's news, or this customer's order history.
2. **Hallucination.** When it doesn't know, it often makes something up that *sounds* right. There's no built-in "I'm not sure."
3. **No provenance.** Even when it's right, it can't tell you *where* the answer came from. Enterprises need citations.

RAG fixes all three by grounding the model in retrieved documents: the knowledge is fresh (you control the data), hallucination drops (the answer must come from supplied context), and you get citations (you know which chunks you handed it).

## RAG vs the alternatives (a classic interview question)

| Approach | What it does | Use when | Weakness |
|---|---|---|---|
| **Prompt engineering only** | Better instructions | Knowledge is general/common | Can't add private or fresh facts |
| **Long context** (paste everything) | Dump all docs in the prompt | Small, fixed corpus | Expensive, slow, "lost in the middle", hard limits |
| **Fine-tuning** | Bake knowledge/behavior into weights | You need a *style/skill*, stable domain | Costly to update, still hallucinates facts, no citations |
| **RAG** | Retrieve relevant facts at query time | Knowledge is large, private, or changing; you need citations | Quality depends entirely on retrieval |

The senior-level nuance: **these are not mutually exclusive.** Real systems often fine-tune for *format/behavior*, use RAG for *facts*, and prompt-engineer the glue. Fine-tuning teaches the model *how to act*; RAG tells it *what is true right now*.

## The three layers (your permanent mental model)

```
                    INDEXING  (offline, runs when data changes)
   docs ──► load ──► chunk ──► embed ──► store in vector index
                                                   │
                    ──────────────────────────────┼──────────────────────
                                                   │
                    RETRIEVAL (online, per query)  ▼
   user query ──► embed query ──► search index ──► top-k chunks ──► (rerank)
                                                   │
                    GENERATION (online, per query) ▼
   prompt = system + retrieved chunks + question ──► LLM ──► grounded answer + citations
```

Memorize this. In an interview you will draw it. In debugging you will walk it top to bottom to find where quality broke.

### Indexing (offline)
Done ahead of time, re-run only when documents change. Steps:
- **Load**: get raw text out of PDFs, HTML, Word, databases, etc.
- **Chunk**: split into pieces small enough to embed and to fit in a prompt, big enough to be meaningful. (Doc 03.)
- **Embed**: turn each chunk into a vector — a list of numbers capturing meaning. (Doc 02.)
- **Store**: put vectors + the original text + metadata into a vector database. (Doc 04.)

> Architect's truth: **retrieval quality is decided during indexing.** ~80% of RAG failures trace back to loading/chunking, not the LLM. If the right chunk isn't in the index in a findable form, no amount of prompt-tuning saves you.

### Retrieval (online)
- Embed the user's query with the *same* model used for the chunks.
- Find the nearest chunk vectors (similarity search).
- Optionally **rerank** to put the truly relevant ones on top. (Doc 05.)

### Generation (online)
- Build a prompt: a system instruction ("answer only from the context, cite sources, say you don't know if it's not there"), the retrieved chunks, and the question.
- The LLM writes the answer. You return it with citations. (Doc 06.)

## A minimal RAG, in pseudocode

```python
# INDEX (once)
chunks = chunk(load("docs/"))
index  = store([(c, embed(c)) for c in chunks])

# QUERY (each time)
def answer(question):
    q_vec   = embed(question)
    top     = index.search(q_vec, k=4)         # retrieval
    context = "\n\n".join(c.text for c in top)
    prompt  = f"Answer using ONLY this context:\n{context}\n\nQ: {question}"
    return llm(prompt)                          # generation
```

`projects/01_hello_rag` is exactly this, written out in real, runnable Python with no framework — so you see every moving part.

## Key vocabulary (full list in `docs/12_glossary.md`)

- **Chunk**: a piece of a document that gets embedded and retrieved.
- **Embedding / vector**: numeric representation of meaning; similar text → nearby vectors.
- **Top-k**: how many chunks you retrieve per query.
- **Context window**: max tokens the LLM can read at once; your chunks must fit.
- **Grounding**: forcing the answer to come from retrieved context.
- **Hallucination**: confident output not supported by the context.

## What "good" looks like (so you know what you're aiming at)

A good RAG answer is: **correct, grounded in the retrieved chunks, cited, and honest when the answer isn't in the data.** Later you'll measure exactly this with four numbers (faithfulness, answer relevancy, context precision, context recall — Doc 07). For now, internalize the goal: *don't just sound right — be right, from the documents, and prove it.*

## Day 1 checklist

- [ ] I can draw the three layers from memory.
- [ ] I can explain RAG vs fine-tuning vs long context and when each wins.
- [ ] I understand why "retrieval quality is set during indexing."
- [ ] I've built and run `projects/01_hello_rag` and made it say "I don't know."

➡️ Next: build `projects/01_hello_rag`, then read `docs/02_embeddings_and_vectors.md`.
