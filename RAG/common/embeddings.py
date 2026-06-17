"""OpenAI embeddings with a tiny on-disk cache so you never pay to embed the same text twice.

Usage:
    from common.embeddings import embed_texts, embed_query
    vecs = embed_texts(["hello", "world"])   # list[list[float]]
    q    = embed_query("hello")              # list[float]
"""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache

from dotenv import load_dotenv

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_REPO_ROOT, ".env"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
_CACHE_DIR = os.path.join(_REPO_ROOT, "common", ".embedding_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    return OpenAI()


def _cache_path(text: str) -> str:
    key = hashlib.sha256((EMBEDDING_MODEL + "::" + text).encode("utf-8")).hexdigest()
    return os.path.join(_CACHE_DIR, key + ".json")


def embed_texts(texts: list[str], *, batch_size: int = 128) -> list[list[float]]:
    """Embed a list of texts. Caches each text individually on disk."""
    results: list[list[float] | None] = [None] * len(texts)
    to_compute: list[int] = []

    # 1. fill from cache
    for i, t in enumerate(texts):
        p = _cache_path(t)
        if os.path.exists(p):
            with open(p) as f:
                results[i] = json.load(f)
        else:
            to_compute.append(i)

    # 2. compute the misses in batches
    client = _client()
    for start in range(0, len(to_compute), batch_size):
        idxs = to_compute[start : start + batch_size]
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=[texts[i] for i in idxs])
        for j, item in zip(idxs, resp.data):
            results[j] = item.embedding
            with open(_cache_path(texts[j]), "w") as f:
                json.dump(item.embedding, f)

    return results  # type: ignore[return-value]


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]


if __name__ == "__main__":
    v = embed_query("retrieval augmented generation")
    print(f"model={EMBEDDING_MODEL} dim={len(v)} first5={v[:5]}")
