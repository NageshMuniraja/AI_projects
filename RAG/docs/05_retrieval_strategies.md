# 05 · Retrieval Strategies

> Day 5. If you master one chapter, make it this one. Retrieval quality is the ceiling on your whole system.

## The mantra

**You cannot generate a good answer from bad context.** Generation is downstream of retrieval. So most of the engineering effort in a serious RAG system goes here.

## Start: pure vector (dense) retrieval

Embed the query, find the k nearest chunk vectors. This is **semantic** — it finds meaning even when words differ. But it has blind spots:
- It can miss **exact terms**: product codes, error numbers, names, acronyms, rare jargon. "Error E-4021" may embed near lots of error text but not the one chunk that names E-4021.
- It can return **topically similar but wrong** chunks.

## Add: keyword (sparse) retrieval — BM25

**BM25** is classic keyword search (think Elasticsearch). It scores chunks by term overlap with the query, weighting rare terms higher. It nails exact matches, codes, and names — exactly where vectors are weak. But it's blind to synonyms and paraphrase.

So: **dense and sparse have opposite weaknesses.** That's the whole motivation for combining them.

## Combine: Hybrid retrieval + Reciprocal Rank Fusion (RRF)

Run vector search and BM25 **in parallel**, then merge their ranked lists. You can't just add scores (cosine ∈ [−1,1], BM25 ∈ [0, big] — incomparable). The clean, score-agnostic way is **Reciprocal Rank Fusion**:

```
RRF_score(chunk) = Σ over each list  1 / (k + rank_in_that_list)     # k≈60
```

A chunk ranked high in *either* list floats up; a chunk ranked high in *both* wins. RRF only uses **ranks**, so it sidesteps the score-scale problem entirely.

**Hybrid is the 2026 default** and typically improves recall by ~1–9% over pure vector, more on corpora full of names/codes. You implement exactly this (BM25 + vector + RRF) in `projects/04_hybrid_search`.

```python
def rrf(rank_lists, k=60):
    scores = {}
    for ranked in rank_lists:                 # each is [chunk_id, chunk_id, ...] best-first
        for rank, cid in enumerate(ranked):
            scores[cid] = scores.get(cid, 0) + 1 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)
```

## Then: Reranking (cross-encoders)

Retrieval gives you, say, the top 20 candidates fast. A **reranker** then re-scores those 20 with a heavier, more accurate model and keeps the top 4–5.

- **Bi-encoder** (your embedding model): encodes query and chunk *separately* → fast, used for the first-pass search over millions.
- **Cross-encoder** (the reranker): reads query **and** chunk *together* → far more accurate relevance judgment, but too slow to run over the whole corpus.

So the pattern is **retrieve wide and cheap (top-20 with hybrid), then rerank narrow and accurate (to top-4)**. This single step is one of the biggest, cheapest quality wins in RAG. In `04_hybrid_search` you use a local `sentence-transformers` cross-encoder (free, no API). In production you might use a hosted reranker (e.g., Cohere Rerank) for convenience.

## The full retrieval pipeline you're building toward

```
query
  ├─► vector search  ─► top 20
  ├─► BM25 search    ─► top 20
  │        └──► RRF fuse ─► top 20 candidates
  └─► cross-encoder rerank ─► top 4  ─► to the prompt
```

## Other knobs that matter

- **top-k**: how many chunks reach the LLM. Too few → missing info; too many → noise + cost + "lost in the middle." Typical: retrieve 20, rerank to 3–5.
- **MMR (Maximal Marginal Relevance)**: when your top results are near-duplicates, MMR trades a little relevance for **diversity** so you don't fill the context with five copies of the same paragraph.
- **Metadata filters**: combine semantic search with hard filters (date, source, permissions) — see Doc 04.
- **Query transformations** (Doc 08): rewriting/expanding the query before retrieval — multi-query, HyDE, decomposition.

## "Lost in the middle"

LLMs attend best to the **start and end** of their context and can overlook facts buried in the middle. Practical consequences:
- Don't dump 20 chunks in; rerank to a handful.
- Put the most relevant chunk **first** (and optionally repeat key context at the end).
- Shorter, higher-precision context often beats longer, lower-precision context.

## How you'll *prove* any of this helped

Every change here is a hypothesis. On Day 7 you'll run the **eval harness** and confirm that hybrid+rerank actually beats naive vector search *on your data* with numbers (context precision/recall, faithfulness). Never ship a retrieval change you didn't measure.

## Interview soundbites

- "Dense retrieval captures meaning; sparse/BM25 captures exact terms; hybrid + RRF gets both and is the 2026 default."
- "RRF fuses by rank, so it ignores incompatible score scales."
- "Bi-encoders retrieve wide and cheap; cross-encoder rerankers re-score narrow and accurate — retrieve 20, rerank to 4."
- "Watch 'lost in the middle': rerank down to a few chunks and order by relevance."

➡️ Next: `docs/06_generation_and_prompting.md`.
