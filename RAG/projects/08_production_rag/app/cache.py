"""Semantic cache: return a previous answer when a new query is similar enough.

This is one of the biggest latency + cost wins in production RAG (doc 11). An exact-string
cache only catches identical queries; a semantic cache catches paraphrases.
"""
from __future__ import annotations

import time

import numpy as np


class SemanticCache:
    def __init__(self, threshold: float = 0.95, ttl_seconds: float = 3600):
        self.threshold = threshold      # cosine similarity needed for a hit
        self.ttl = ttl_seconds
        self._vecs: list[np.ndarray] = []
        self._entries: list[dict] = []  # {"query","answer","ts"}
        self.hits = 0
        self.misses = 0

    def get(self, query_vec: list[float]):
        q = np.asarray(query_vec, dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-12)
        now = time.time()
        best_i, best_sim = -1, -1.0
        for i, v in enumerate(self._vecs):
            if now - self._entries[i]["ts"] > self.ttl:
                continue
            sim = float(v @ q)
            if sim > best_sim:
                best_i, best_sim = i, sim
        if best_i >= 0 and best_sim >= self.threshold:
            self.hits += 1
            return self._entries[best_i]["answer"], best_sim
        self.misses += 1
        return None, best_sim

    def put(self, query: str, query_vec: list[float], answer: dict):
        v = np.asarray(query_vec, dtype=np.float32)
        v = v / (np.linalg.norm(v) + 1e-12)
        self._vecs.append(v)
        self._entries.append({"query": query, "answer": answer, "ts": time.time()})

    def stats(self):
        total = self.hits + self.misses
        return {"size": len(self._entries), "hits": self.hits, "misses": self.misses,
                "hit_rate": round(self.hits / total, 3) if total else 0.0}
