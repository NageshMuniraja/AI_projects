# Project 03 — Chunking Lab

**Level:** Intermediate · **Day:** 3 · **Read first:** `docs/03_chunking_strategies.md`

Chunking can swing RAG accuracy more than any other single change. This lab makes that visible: four strategies, one document, the same questions — you watch the retrieved chunk change.

## Run it

```bash
cd projects/03_chunking_lab
python chunking_lab.py
python chunking_lab.py --query "what happens when a host gets too hot?"
```

It prints how many chunks each strategy produces (and their token sizes), then for each query shows the **top-matching chunk under each strategy** with its similarity score.

## The four strategies

- **fixed** — fixed token windows, no overlap. Fast, dumb, cuts mid-idea.
- **overlap** — fixed windows with overlap so boundary-straddling facts survive. The sane default.
- **recursive** — packs paragraphs/sentences up to a budget; respects document structure.
- **semantic** — starts a new chunk when consecutive sentences become dissimilar (topic shift). Costs embeddings at index time; often cleanest chunks.

## What to look for

1. **Boundary damage:** find a query whose answer sits at a chunk boundary. `fixed` often splits it; `overlap`/`recursive` keep it whole.
2. **Blurry big chunks:** when a chunk covers several topics, its score is *lower* for a specific question (the embedding is an average). Semantic/recursive chunks score higher because they isolate one idea.
3. **No universal winner:** different queries favor different strategies. That's the lesson — you can't eyeball "best"; you **measure** on your data (Project 05).

## Stretch goals

1. **Break each strategy.** Craft one query that `fixed` gets wrong but `semantic` gets right, and one where they tie. Explain why.
2. **Tune the knobs.** Change `size`/`overlap` and the semantic `threshold`. Watch chunk counts and scores move.
3. **Token vs character.** This lab counts tokens. Add a character-based variant and compare chunk boundaries.
4. **Add contextual prefixing (Doc 08 preview).** Prepend the section heading to each chunk before embedding and see if scores rise.
5. **Carry results forward.** Pick the strategy/size that looks best here, then *prove* it with numbers in Project 05's eval harness.

## Concepts made concrete

- Every chunking strategy from Doc 03, and the precision-vs-context tension
- Why "80% of RAG failures start in ingestion"
- The handoff to evaluation: intuition here, proof in Project 05
