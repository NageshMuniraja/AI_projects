"""Project 04 — Hybrid search: BM25 + vector + Reciprocal Rank Fusion + cross-encoder rerank.

This is the retrieval pipeline most production RAG systems actually use (doc 05).
You will SEE keyword search win on codes/names (E-4021, Abyss) and vector search win on
paraphrases ("getting your money back" -> Refunds), and hybrid+rerank get both.

Run:
    python hybrid_search.py
    python hybrid_search.py --query "how do I get my money back?"
    python hybrid_search.py --query "what is error E-4021" --no-rerank
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import numpy as np
from rank_bm25 import BM25Okapi

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.embeddings import embed_query, embed_texts  # noqa: E402

CORPUS = os.path.join(os.path.dirname(__file__), "data", "corpus.md")


def load_passages(path: str) -> list[str]:
    text = open(path, encoding="utf-8").read()
    # each "## heading\n body" becomes one passage (heading + body)
    parts = re.split(r"\n##\s+", text)
    passages = []
    for p in parts[1:]:  # skip the file preamble before the first ##
        lines = p.strip().splitlines()
        title = lines[0].strip()
        body = " ".join(l.strip() for l in lines[1:]).strip()
        passages.append(f"{title}. {body}")
    return passages


def tokenize(s: str) -> list[str]:
    return re.findall(r"[a-z0-9\-]+", s.lower())


# ----------------------------- the three retrievers -----------------------------
def vector_rank(query: str, vecs: np.ndarray, n: int) -> list[int]:
    q = np.array(embed_query(query), dtype=np.float32)
    q /= np.clip(np.linalg.norm(q), 1e-12, None)
    scores = vecs @ q
    return list(np.argsort(scores)[::-1][:n])


def bm25_rank(query: str, bm25: BM25Okapi, n: int) -> list[int]:
    scores = bm25.get_scores(tokenize(query))
    return list(np.argsort(scores)[::-1][:n])


def rrf_fuse(rank_lists: list[list[int]], k: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for ranked in rank_lists:
        for rank, idx in enumerate(ranked):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)


# ----------------------------- reranker (cross-encoder) -----------------------------
def get_reranker():
    try:
        from sentence_transformers import CrossEncoder

        return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] reranker unavailable ({e}); continuing without rerank.")
        return None


def rerank(reranker, query: str, candidate_idxs: list[int], passages: list[str], top_k: int):
    pairs = [(query, passages[i]) for i in candidate_idxs]
    scores = reranker.predict(pairs)
    order = np.argsort(scores)[::-1]
    return [(candidate_idxs[o], float(scores[o])) for o in order[:top_k]]


def show(title, idxs, passages, scores=None):
    print(f"\n{title}")
    for rank, i in enumerate(idxs):
        s = f" ({scores[rank]:.2f})" if scores is not None else ""
        print(f"  {rank+1}. [{i}]{s} {passages[i][:70]}...")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default=None)
    ap.add_argument("--candidates", type=int, default=6, help="how many each retriever returns before fusion")
    ap.add_argument("--top-k", type=int, default=3, help="final results after rerank")
    ap.add_argument("--no-rerank", action="store_true")
    args = ap.parse_args()

    passages = load_passages(CORPUS)
    vecs = np.array(embed_texts(passages), dtype=np.float32)
    vecs /= np.clip(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-12, None)
    bm25 = BM25Okapi([tokenize(p) for p in passages])
    reranker = None if args.no_rerank else get_reranker()

    queries = [args.query] if args.query else [
        "what is error E-4021?",            # keyword should shine (exact code)
        "how do I get my money back?",      # vector should shine (paraphrase of Refunds)
        "where does Helios send poison messages?",  # name 'Abyss' -> hybrid helps
    ]

    for q in queries:
        print("=" * 80)
        print(f"QUERY: {q}")
        v = vector_rank(q, vecs, args.candidates)
        b = bm25_rank(q, bm25, args.candidates)
        fused = rrf_fuse([v, b])

        show("Vector-only top:", v[:args.top_k], passages)
        show("BM25-only top:", b[:args.top_k], passages)
        show("Hybrid (RRF) top:", fused[:args.top_k], passages)

        if reranker is not None:
            reranked = rerank(reranker, q, fused[: max(args.candidates, args.top_k * 2)], passages, args.top_k)
            show("Hybrid + rerank top:", [i for i, _ in reranked], passages, [s for _, s in reranked])
        print()

    print("Takeaway: keyword nails exact codes/names; vectors nail paraphrase; "
          "RRF fuses both; the cross-encoder reranker fixes the final ordering. (doc 05)")


if __name__ == "__main__":
    main()
