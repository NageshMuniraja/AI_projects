"""Provider-agnostic chat completion.

Reads .env from the repo root. Default provider is OpenAI; set LLM_PROVIDER=anthropic
to route generation through Claude. Embeddings always use OpenAI (see embeddings.py).

Usage:
    from common.llm import chat
    answer = chat("You are helpful.", "What is RAG?")
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

# Load .env from repo root no matter which project runs this.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_REPO_ROOT, ".env"))

PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")


@lru_cache(maxsize=1)
def _openai_client():
    from openai import OpenAI

    return OpenAI()  # reads OPENAI_API_KEY from env


@lru_cache(maxsize=1)
def _anthropic_client():
    from anthropic import Anthropic

    return Anthropic()  # reads ANTHROPIC_API_KEY from env


def chat(
    system: str,
    user: str,
    *,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    model: str | None = None,
) -> str:
    """Single-turn chat completion. Returns the assistant text.

    temperature=0.0 by default because RAG answers should be deterministic and grounded.
    """
    if PROVIDER == "anthropic":
        client = _anthropic_client()
        resp = client.messages.create(
            model=model or ANTHROPIC_MODEL,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text

    # default: openai
    client = _openai_client()
    resp = client.chat.completions.create(
        model=model or OPENAI_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content


def chat_messages(messages: list[dict], *, temperature: float = 0.0, max_tokens: int = 1024) -> str:
    """Multi-turn version taking a full messages list (OpenAI format)."""
    if PROVIDER == "anthropic":
        client = _anthropic_client()
        system = ""
        conv = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                conv.append(m)
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=conv,
        )
        return resp.content[0].text

    client = _openai_client()
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages,
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    print(f"Provider: {PROVIDER}")
    print(chat("You are concise.", "In one sentence, what is retrieval-augmented generation?"))
