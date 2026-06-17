# Project 01 — Hello RAG (from scratch)

**Level:** Beginner · **Day:** 1–2 · **Read first:** `docs/01_rag_fundamentals.md`, `docs/02_embeddings_and_vectors.md`

The entire RAG loop in ~120 lines of plain Python, **no framework**. Every step is visible: chunk → embed → cosine-search → grounded generate. If you understand this file, you understand RAG. Everything else in the repo is making each step better.

## Run it

```bash
# from repo root, with .venv active and .env filled in
cd projects/01_hello_rag
python hello_rag.py
# or ask your own:
python hello_rag.py "How do refunds work after 40 days?"
```

First run embeds the chunks (cached to disk afterward, so re-runs are instant and free).

## What to watch

The script prints the **retrieved chunks and their cosine scores** for each question. This is the most important habit in RAG: *look at what was retrieved before judging the answer.* Notice:

- The two answerable questions pull chunks with clearly higher scores.
- "Can I pay with Dogecoin?" pulls only weak/irrelevant chunks → the **relevance gate** triggers a refusal instead of a hallucination.

## Minimum viable (today)

Run it, read the code top to bottom, and make sure you can name what each of the 5 functions does.

## Stretch goals (the learning is here)

1. **Force a hallucination, then prevent it.** Lower `min_score` to `-1` so the gate never triggers, ask "Can I pay with Dogecoin?", and watch it guess. Put the gate back. This is *why* grounding + gating exist.
2. **Tune chunking.** Change `chunk_size`/`overlap` (try 300/50 and 1000/0). Re-run a question that spans two policies. How does retrieval change? (Preview of `docs/03`.)
3. **Swap the embedding model.** In `.env`, set `EMBEDDING_MODEL=text-embedding-3-large`, delete `common/.embedding_cache/`, re-run. Did the ranking of retrieved chunks change for your hardest question?
4. **Print a similarity matrix.** Embed `["cat","kitten","feline","invoice"]` and print pairwise cosine. Confirm the animals cluster and "invoice" is far away.
5. **Add a 4th chunk to the answer (k=4)** and see whether more context helps or just adds noise.

## Concepts this project makes concrete

- Chunking, embeddings, cosine similarity, top-k retrieval (Docs 02–03)
- Grounded prompting + refusal / relevance gate (Doc 06)
- Why "retrieval quality is set during indexing" (Doc 01)

## Common issues

- `AuthenticationError` → `.env` not filled or venv not active (see `SETUP.md`).
- Answer seems wrong → **look at the printed chunks first.** If the right chunk wasn't retrieved, it's a retrieval problem (chunking/embedding), not a prompt problem.
