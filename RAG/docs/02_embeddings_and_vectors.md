# 02 · Embeddings & Vector Math

> Day 2. The math is light; the intuition is everything.

## What an embedding actually is

An **embedding** is a function that turns text into a fixed-length list of numbers (a *vector*) such that **text with similar meaning lands at nearby points** in that high-dimensional space.

- `text-embedding-3-small` outputs **1536 numbers** per input.
- "dog" and "puppy" → vectors close together. "dog" and "tax law" → far apart.
- The model learned this geometry from huge amounts of text; you just call an API.

You don't interpret the individual numbers. You only ever care about **distances/angles between vectors**.

## Why this powers retrieval

Keyword search matches *strings*. Embeddings match *meaning*. If a user asks "how do I reset my password?" and the doc says "steps to recover account credentials," keyword search finds nothing useful — but the embeddings are close, so vector search finds it. This is **semantic search**, and it's the heart of retrieval.

## Measuring similarity

Three common ways to score how "close" two vectors are:

| Metric | Formula idea | Range | Notes |
|---|---|---|---|
| **Cosine similarity** | angle between vectors | −1 … 1 (1 = identical direction) | The default for text embeddings. Ignores magnitude, cares about direction. |
| **Dot product** | cosine × magnitudes | unbounded | Same as cosine **if vectors are normalized** (length 1). Fast. |
| **Euclidean (L2)** | straight-line distance | 0 … ∞ (0 = identical) | Smaller = closer. Common in some indexes. |

**Cosine is the standard choice for text.** OpenAI embeddings are normalized, so cosine and dot product give the same ranking — which is why many vector DBs default to one or the other for speed.

Cosine similarity in code:

```python
import numpy as np

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
```

In `01_hello_rag` you compute this yourself and rank chunks by it. Seeing the raw scores once is worth ten tutorials.

## Choosing an embedding model (2026)

| Model | Dim | Notes |
|---|---|---|
| `text-embedding-3-small` | 1536 | Cheap, fast, strong. **Default for this repo.** |
| `text-embedding-3-large` | 3072 | More accurate, ~6× cost, larger vectors → more storage/compute. |
| Open-source (e.g. BGE, E5, GTE families) | varies | Run locally/free; great for privacy or cost at scale. |

Rules of thumb:
- Start with `-3-small`. Only move to `-large` if evaluation (Doc 07) shows retrieval is your bottleneck.
- **You must use the same model for indexing and querying.** Embeddings from different models live in different spaces and aren't comparable.
- Bigger dimension ≠ always better; it costs more storage and slightly slower search. Some models support **Matryoshka** truncation (use the first N dims) to trade accuracy for size.

## Things that quietly break embedding quality

- **Garbage in:** PDF extraction artifacts, headers/footers, nav menus, and boilerplate get embedded too and pollute results. Clean during loading.
- **Chunks too big:** one vector trying to represent five topics is a blurry average that matches everything weakly. (Doc 03.)
- **Mixed languages / domains:** a general model may underperform on, say, legal or medical jargon. Domain-specific models help.
- **Asymmetric search:** a short query vs a long passage. Some models have separate "query" and "document" prompts/prefixes — use them if the model recommends it.

## Cost & performance intuition

- Embedding is **cheap and one-time** per chunk (cache it — this repo persists embeddings to disk so you never pay twice).
- A query embeds **one** string, then the search is pure math against stored vectors — fast.
- The expensive online cost is almost always the **LLM generation**, not the embedding.

## Mini-experiments to actually understand this (do these on Day 2)

1. Embed "cat", "kitten", "feline", "automobile". Print the cosine matrix. Confirm the first three cluster and "automobile" is the odd one out.
2. In `01_hello_rag`, print the top-k chunks *with their cosine scores*. Ask a question the docs answer well (scores ~0.5+) and one they don't (scores low/flat). Notice how flat low scores are the signal for "I don't know."
3. Re-embed your corpus with `-3-large` and see whether the *ranking* of retrieved chunks changes for your hardest query.

## Interview soundbites

- "Embeddings map text to a vector space where semantic similarity = geometric proximity; we retrieve by nearest-neighbor search, usually cosine."
- "Same model for index and query, always — they must share a vector space."
- "Embedding cost is trivial and cacheable; the online cost and latency are dominated by generation."

➡️ Next: `docs/03_chunking_strategies.md`, then `projects/03_chunking_lab`.
