# Project 02 — PDF Q&A with a real vector DB + citations

**Level:** Beginner+ · **Day:** 4 (revisit Day 6) · **Read first:** `docs/04_vector_databases.md`, then `docs/06_generation_and_prompting.md`

Project 01 kept everything in memory and computed similarity by hand. Real systems use a **vector database**. Here you ingest a real **PDF** into **Chroma** (persistent on disk), retrieve with metadata, and return answers **with citations** (source + page). You also get **metadata filtering**.

## Files

- `ingest.py` — load PDF → token-chunk → embed → upsert into Chroma with `{source, page}` metadata.
- `ask.py` — embed query → Chroma similarity search → grounded, **cited** answer (with a refusal gate + optional `--source` filter).
- `data/helios_policies.pdf` — a multi-page sample document (swap in your own PDFs anytime).

## Run it

```bash
cd projects/02_pdf_qa
python ingest.py --reset                       # build the index (idempotent; re-run anytime)
python ask.py "How long is the free trial and do I need a card?"
python ask.py "What service credit do I get at 98.5% uptime?"
python ask.py "Can I pay with Dogecoin?"       # not in the docs -> refuses
python ask.py "What regions exist?" --source helios_policies.pdf   # metadata filter
```

Each answer prints the **sources used** (filename + page + similarity score) so you can verify grounding.

## What's new vs Project 01

- **Persistent vector store** (Chroma) instead of an in-memory numpy matrix — survives restarts, scales past memory.
- **Token-based chunking** (`tiktoken`) instead of character counts — closer to how limits/cost actually work.
- **Metadata + citations** — every chunk carries `source` and `page`; answers cite them.
- **Idempotent upserts** — stable chunk IDs (`file:pN:cM`) mean re-ingesting updates rather than duplicating.
- **Metadata filtering** — `--source` restricts search to one document (the basis of per-tenant access control, Doc 11).

## Minimum viable (today)

Ingest, ask the four demo questions, and confirm the citations point at the right pages.

## Stretch goals

1. **Add your own PDF.** Drop any PDF in `data/`, re-run `ingest.py`, and ask about it. Watch what happens with a scanned/image PDF (no extractable text) — that's a real-world ingestion failure (Doc 03).
2. **Tighten the gate.** Find a borderline question and tune `min_score` so it refuses bad context but still answers good questions.
3. **Filtering as security.** Ingest two PDFs, then prove `--source` only ever returns chunks from the allowed file. That mechanism is how you stop cross-tenant data leaks.
4. **Citation audit.** After an answer, check that every `(file, p.N)` it cited is actually in the printed "Sources used" list. (You'll automate this idea in Project 05.)
5. **Chunk-size experiment.** Change `size`/`overlap` in `ingest.py`, `--reset`, and see how answers/citations shift. Save your observations for Project 03.

## Concepts made concrete

- Vector DBs, persistence, HNSW cosine space, metadata filtering (Doc 04)
- Citations, grounded prompting, refusal gate (Doc 06)
- Idempotent ingestion / upserts (Doc 11)

## Common issues

- `chromadb` errors about sqlite → use Python 3.10+ (see `SETUP.md`).
- "I don't have enough information…" on a question you *know* is in the PDF → inspect the printed sources; likely a chunking/retrieval miss. Try `--k 6` or smaller chunks.
- Empty retrieval → did you run `ingest.py` first? Is the PDF text-based (not a scan)?
