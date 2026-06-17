"""Run this after setup:  python common/check_setup.py

Verifies env, API connectivity, embeddings, a chat completion, and local libs.
Prints ✅ / ❌ for each check and a final summary.
"""
from __future__ import annotations

import os
import sys

OK = "✅"
BAD = "❌"


def main() -> int:
    failures = 0

    # 1. .env loaded
    try:
        from dotenv import load_dotenv

        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        load_dotenv(os.path.join(root, ".env"))
        provider = os.getenv("LLM_PROVIDER", "openai")
        print(f"{OK} .env loaded (LLM_PROVIDER={provider})")
    except Exception as e:  # noqa: BLE001
        print(f"{BAD} could not load .env: {e}")
        return 1

    # 2. required key present
    if os.getenv("OPENAI_API_KEY", "").startswith("sk-") and "replace" not in os.getenv("OPENAI_API_KEY", ""):
        print(f"{OK} OPENAI_API_KEY present")
    else:
        print(f"{BAD} OPENAI_API_KEY missing or still the placeholder — edit .env")
        failures += 1

    # 3. embeddings
    try:
        from common.embeddings import embed_query

        v = embed_query("hello world")
        print(f"{OK} embeddings work (dim={len(v)})")
    except Exception as e:  # noqa: BLE001
        print(f"{BAD} embeddings failed: {e}")
        failures += 1

    # 4. chat completion
    try:
        from common.llm import chat

        out = chat("You are concise.", "Reply with the single word: ready")
        print(f"{OK} chat completion works (model replied: {out.strip()[:40]!r})")
    except Exception as e:  # noqa: BLE001
        print(f"{BAD} chat completion failed: {e}")
        failures += 1

    # 5. local libraries
    libs = ["chromadb", "rank_bm25", "sentence_transformers", "ragas", "langchain", "fastapi", "networkx"]
    missing = []
    for lib in libs:
        try:
            __import__(lib)
        except Exception:  # noqa: BLE001
            missing.append(lib)
    if missing:
        print(f"{BAD} missing libraries: {', '.join(missing)} — run: pip install -r requirements.txt")
        failures += 1
    else:
        print(f"{OK} local libraries importable ({', '.join(libs)})")

    print("\n" + ("All checks passed. You're ready for Day 1." if failures == 0 else f"{failures} check(s) failed — fix the ❌ items above."))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    # allow "from common..." imports when run from repo root
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    raise SystemExit(main())
