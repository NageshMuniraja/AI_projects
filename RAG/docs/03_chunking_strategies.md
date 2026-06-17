# 03 · Chunking Strategies

> Day 3. This chapter is short to read and huge in impact. Changing chunking can swing accuracy by 80%+ — more than swapping models.

## Why we chunk at all

You can't embed a 50-page PDF as one vector (it'd be a meaningless average) and you can't paste it all into every prompt (cost, latency, context limits, "lost in the middle"). So you split documents into **chunks**: pieces small enough to embed precisely and to fit several into a prompt, large enough to carry a complete thought.

**The chunk is the unit of retrieval.** You retrieve chunks, not documents. So the question "what is a good chunk?" *is* the question "what is good retrieval?"

## The core tension

- **Too small** (e.g., one sentence): precise match, but missing surrounding context → the LLM gets a fragment it can't reason over.
- **Too big** (e.g., a whole section): rich context, but the embedding is a blurry average of many ideas → matches weakly, retrieves irrelevant neighbors, wastes context window.

You're tuning for the sweet spot, and the sweet spot depends on your documents and your questions.

## Strategies, from naive to smart

### 1. Fixed-size
Split every N characters/tokens. Dead simple, fast, but blindly cuts mid-sentence and mid-idea.

### 2. Fixed-size with overlap
Same, but each chunk repeats the last ~10–20% of the previous one. The overlap means a fact that straddles a boundary still appears intact in at least one chunk. **This is the sane default.**

### 3. Recursive character splitting
Try to split on the biggest natural boundary first (paragraphs `\n\n`), then sentences, then words, only falling back to hard cuts if a piece is still too big. Respects structure far better than fixed-size. (LangChain's `RecursiveCharacterTextSplitter` is the common implementation.)

### 4. Document-structure-aware
Use the document's own structure: Markdown headings, HTML tags, PDF sections, code functions. Keep a heading with its body; never split a table row from its header. Best when your docs are well-structured.

### 5. Semantic chunking
Embed sentences, then start a new chunk when the topic *shifts* (a drop in similarity between consecutive sentences). Chunks follow meaning, not character counts. More compute at index time; often better retrieval. (`03_chunking_lab` implements a simple version.)

### 6. Late / contextual approaches (2026, advanced)
- **Contextual retrieval**: prepend a one-line LLM-generated summary of *where this chunk sits in the document* before embedding it ("This chunk is from the 2025 refund-policy section and discusses…"). Big recall gains; you pay an LLM call per chunk at index time.
- **Parent-document / small-to-big**: embed small chunks for precise *matching*, but return the larger *parent* chunk for the LLM to read. Best of both — covered in Doc 08.

## The numbers to start from (2026 benchmarks)

A widely-validated default: **~512 tokens per chunk with 10–20% overlap (≈50–100 tokens).** It scored highest composite accuracy across real-world document sets in early-2026 evaluations. But "default" ≠ "optimal for you."

**Don't guess — sweep and measure.** Test at minimum these and score each with RAGAS context precision/recall (Doc 07):

| chunk_size | overlap |
|---|---|
| 256 | 32 |
| 512 | 64 |
| 512 | 100 |
| 1024 | 128 |

Pick the configuration with the best context precision *and* recall for *your* corpus and *your* questions. That's the whole game in `03_chunking_lab`.

## Metadata: the underrated half of chunking

When you store a chunk, also store **metadata**: source filename, page number, section heading, document date, author, access permissions. This buys you:
- **Citations** ("from refund_policy.pdf, p.4").
- **Filtering** ("only search 2026 docs" / "only docs this user may see").
- **Debuggability** (you can see *which* chunk produced a bad answer).

Treat metadata as mandatory, not optional. It's how RAG becomes auditable and secure.

## A decision guide

- Prose docs (wikis, reports, PDFs) → **recursive split, 512/64**, then tune.
- Highly structured docs (Markdown, HTML, API docs) → **structure-aware** split on headings.
- Code → split on functions/classes.
- FAQ / Q&A pairs → **one chunk per Q&A**; don't split a question from its answer.
- Tables → keep each row with its header; consider converting tables to text sentences.
- Very long, topic-shifting docs → **semantic chunking** or contextual retrieval.

## Interview soundbites

- "Chunking is the highest-leverage knob in RAG; ~80% of failures originate in ingestion/chunking, not the model."
- "Default to recursive splitting around 512 tokens with ~15% overlap, then sweep sizes and pick by RAGAS context precision/recall."
- "Always attach metadata — it's what gives you citations, filtering, and security."
- "Small-to-big: embed small for matching, return big for reading."

➡️ Next: `docs/04_vector_databases.md`, then `projects/02_pdf_qa`.
