# Project 04 — Hybrid Search (BM25 + Vector + RRF + Rerank)

**Level:** Intermediate · **Day:** 5 (extend Day 8) · **Read first:** `docs/05_retrieval_strategies.md`

The retrieval pipeline real production systems use. You combine **keyword (BM25)** and **vector** search, fuse them with **Reciprocal Rank Fusion**, then **rerank** the candidates with a cross-encoder — and you watch each piece earn its place.

## Run it

```bash
cd projects/04_hybrid_search
python hybrid_search.py
python hybrid_search.py --query "how do I get my money back?"
python hybrid_search.py --query "what is error E-4021" --no-rerank
```

For each query it prints **four** ranked lists side by side: vector-only, BM25-only, hybrid (RRF), and hybrid+rerank. Comparing them is the whole point.

> First run downloads the cross-encoder model (~80MB) once. If you're offline, pass `--no-rerank`.

## What you'll observe

- **"what is error E-4021?"** → BM25 nails the exact code; pure vector may drift to other error text. Hybrid keeps the right one on top.
- **"how do I get my money back?"** → no shared keywords with "Refunds," so BM25 struggles; vector matches the *meaning*. Hybrid wins.
- **"where does Helios send poison messages?"** → needs both the concept (dead-letter) and the name (Abyss). Hybrid + rerank lands it.

This is the concrete proof of Doc 05's claim: dense and sparse have **opposite** weaknesses, so combining them beats either alone.

## How the pieces work (all in `hybrid_search.py`)

- `bm25_rank` — keyword scoring via `rank_bm25`.
- `vector_rank` — cosine over OpenAI embeddings.
- `rrf_fuse` — merges the two ranked lists by **rank** (`1/(k+rank)`), sidestepping incompatible score scales.
- `rerank` — a `sentence-transformers` **cross-encoder** re-scores the fused candidates (reads query+passage together) and reorders.

## Stretch goals

1. **Find the win for each retriever.** Write one query only BM25 gets right, one only vectors get right, and confirm hybrid gets both.
2. **Weighted fusion.** Modify RRF to weight vector vs BM25 differently; see when it helps/hurts.
3. **Add MMR (Doc 05).** Penalize near-duplicate passages so the top-k is diverse.
4. **Swap the reranker.** Try a different cross-encoder model, or wire in a hosted reranker (e.g., Cohere Rerank) and compare quality/latency.
5. **Hook to generation.** Feed the reranked top-k into the grounded prompt from Project 02 and answer with citations.
6. **Prove it with numbers.** Take this pipeline into Project 05 and show hybrid+rerank beats naive vector on context precision/recall.

## Concepts made concrete

- Dense vs sparse retrieval and their opposite blind spots (Doc 05)
- Reciprocal Rank Fusion and why it ignores score scales
- Bi-encoder (retrieve wide) vs cross-encoder (rerank narrow)
