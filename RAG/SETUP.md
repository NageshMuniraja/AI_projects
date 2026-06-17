# Setup (do this once, before Day 1)

You said you're comfortable with Python and will use a **paid API (OpenAI / Anthropic)**. This repo defaults to **OpenAI** for LLM + embeddings because it has the widest compatibility, and the code is written so you can switch to **Anthropic Claude** for generation with one env var. Everything else (vector DB, BM25, reranker) runs **locally and free**.

## 1. Python

Use Python 3.10–3.12.

```bash
# from the repo root: /Users/nageshmuniraja/Learning_map/RAG
python3 --version            # confirm 3.10+
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

This installs the full toolkit (OpenAI/Anthropic SDKs, Chroma, sentence-transformers, rank-bm25, RAGAS, LangChain, FastAPI, etc.). First install pulls a PyTorch wheel for the local reranker, so it may take a few minutes.

> If you want a lighter start, you can install per-project — each project README lists the few packages it actually needs.

## 3. API keys

Copy the template and fill in your key(s):

```bash
cp .env.example .env
```

Then edit `.env`:

```
OPENAI_API_KEY=sk-...            # required (LLM + embeddings by default)
ANTHROPIC_API_KEY=sk-ant-...     # optional, only if LLM_PROVIDER=anthropic
LLM_PROVIDER=openai              # openai | anthropic
LLM_MODEL=gpt-4o-mini            # cheap + good. Use gpt-4o for harder tasks.
EMBEDDING_MODEL=text-embedding-3-small
```

- Get an OpenAI key: platform.openai.com → API keys.
- Get an Anthropic key: console.anthropic.com → API keys.
- **Never commit `.env`.** It's already in `.gitignore`.

### Cost expectations (2 weeks, this curriculum)
With `gpt-4o-mini` + `text-embedding-3-small` the whole program costs roughly **$5–15** total. Embeddings are pennies; the only spend that adds up is the eval harness (Day 7+) and the agentic loops (Days 9–10), which call the LLM many times. Tips:
- Keep `LLM_MODEL=gpt-4o-mini` for everything except when a project says otherwise.
- Cache embeddings (the projects do this — they persist Chroma to disk so you don't re-embed).
- Set a usage limit in your OpenAI dashboard so you can't be surprised.

## 4. Verify it works

```bash
python common/check_setup.py
```

You should see ✅ for: env loaded, OpenAI reachable, embeddings working, a tiny chat completion, and local libraries importable. If anything fails, the script tells you exactly what to fix.

## 5. Common gotchas

- **`openai.AuthenticationError`** → your key is missing/wrong in `.env`, or you didn't `source .venv/bin/activate`.
- **`ModuleNotFoundError`** → venv not activated, or `pip install -r requirements.txt` didn't finish.
- **Chroma / sqlite errors on old Python** → use Python 3.10+ (Chroma needs a recent sqlite).
- **Slow first run** → `sentence-transformers` downloads the reranker model (~80MB) once, then caches it.
- **Rate limits** → add a small `time.sleep` between calls, or lower batch sizes; the eval harness has a concurrency setting.

You're ready. Go to **ROADMAP.md → Day 1**.
