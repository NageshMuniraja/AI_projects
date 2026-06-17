# RAG: Beginner → Architect

A two-week, hands-on program to take you from zero to architect-level on **Retrieval-Augmented Generation (RAG)**. Built for someone comfortable with Python who is new to RAG and AI.

By the end you will be able to:

- Explain every part of a RAG pipeline and why each exists.
- Build RAG systems from scratch (no framework) *and* with frameworks (LangChain / LlamaIndex).
- Choose chunking, embedding, retrieval, and reranking strategies and **defend the trade-offs**.
- Measure quality with RAGAS and improve a pipeline based on numbers, not vibes.
- Design agentic and graph-based RAG, and ship a production service with caching, observability, and guardrails.
- Walk into an AI Engineer / RAG Architect interview and handle the system-design round.

---

## How this repo is organized

```
RAG/
├── README.md            ← you are here
├── ROADMAP.md           ← the 14-day plan (what to do each day)
├── SETUP.md             ← environment + API keys (do this first)
├── requirements.txt     ← all Python dependencies
├── .env.example         ← copy to .env and add your keys
│
├── docs/                ← the textbook. Read these alongside the projects.
│   ├── 01_rag_fundamentals.md
│   ├── 02_embeddings_and_vectors.md
│   ├── 03_chunking_strategies.md
│   ├── 04_vector_databases.md
│   ├── 05_retrieval_strategies.md
│   ├── 06_generation_and_prompting.md
│   ├── 07_evaluation_ragas.md
│   ├── 08_advanced_rag.md
│   ├── 09_agentic_rag.md
│   ├── 10_graph_rag.md
│   ├── 11_production_architecture.md
│   └── 12_glossary.md
│
├── common/              ← shared helpers used across projects (LLM + embedding clients)
│
├── projects/            ← 8 projects, each harder than the last
│   ├── 01_hello_rag/        Beginner   – RAG from scratch over a text file
│   ├── 02_pdf_qa/           Beginner+  – PDF Q&A with a vector DB + citations
│   ├── 03_chunking_lab/     Intermediate – measure how chunking changes answers
│   ├── 04_hybrid_search/    Intermediate – BM25 + vectors + RRF + reranking
│   ├── 05_eval_harness/     Intermediate+ – RAGAS evaluation pipeline
│   ├── 06_agentic_rag/      Advanced    – query routing + multi-step retrieval
│   ├── 07_graph_rag/        Advanced    – graph + vector hybrid retrieval
│   └── 08_production_rag/   Architect   – FastAPI service, caching, observability
│
└── interview_prep/      ← question bank, system-design playbook, cheat sheet (+ PDFs)
```

## The 3-layer mental model (keep this in your head the whole time)

Every RAG system, no matter how fancy, is three layers:

1. **Indexing (offline):** load documents → chunk → embed → store in a vector index. *Most RAG failures are born here.*
2. **Retrieval (online):** take a user query → find the most relevant chunks → optionally rerank/expand them.
3. **Generation (online):** stuff the best chunks into a prompt → the LLM answers using *only* that context → return the answer with citations.

Projects 1–2 build all three naively. Projects 3–5 make each layer measurably better. Projects 6–8 make the system *intelligent* and *production-ready*.

## How to use this repo each day

1. Read the matching `docs/` chapter (20–40 min).
2. Build / run the matching project (90–120 min).
3. Do the "Stretch goals" in each project README (30–45 min).
4. Review the matching `interview_prep` questions (20–30 min).

That's ~3 hours/day. The full schedule is in **ROADMAP.md**.

## Start here

1. Open **SETUP.md** and get your environment + API key working.
2. Open **ROADMAP.md** and start Day 1.
3. Read `docs/01_rag_fundamentals.md`, then build `projects/01_hello_rag`.

> Tip: don't just run the code. Break it. Change the chunk size, swap the model, ask it a question the documents can't answer, and watch what happens. That instinct is what separates a RAG *user* from a RAG *architect*.
