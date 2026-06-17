"""Project 03 — Chunking Lab.

Compare chunking strategies on the SAME document and SAME questions, and SEE how the
retrieved chunk changes. Chunking is the highest-leverage knob in RAG (doc 03).

Strategies implemented (all from scratch so you see the mechanics):
  - fixed         : fixed token windows, no overlap
  - overlap       : fixed token windows WITH overlap (the sane default)
  - recursive     : split on paragraphs -> sentences, packing up to a size budget
  - semantic      : start a new chunk when topic similarity between sentences drops

Run:
    python chunking_lab.py
    python chunking_lab.py --query "what happens when a host gets too hot?"
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import numpy as np
import tiktoken

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.embeddings import embed_query, embed_texts  # noqa: E402

DOC = os.path.join(os.path.dirname(__file__), "data", "helios_runbook.md")
_enc = tiktoken.get_encoding("cl100k_base")


def n_tokens(text: str) -> int:
    return len(_enc.encode(text))


# ----------------------------- strategies -----------------------------
def chunk_fixed(text: str, size: int = 120, overlap: int = 0) -> list[str]:
    toks = _enc.encode(text)
    out, start = [], 0
    while start < len(toks):
        out.append(_enc.decode(toks[start : start + size]).strip())
        start += size - overlap if size > overlap else size
    return [c for c in out if c]


def chunk_overlap(text: str, size: int = 120, overlap: int = 24) -> list[str]:
    return chunk_fixed(text, size=size, overlap=overlap)


def split_sentences(text: str) -> list[str]:
    # light sentence splitter (good enough for the lab)
    parts = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    return [p.strip() for p in parts if p.strip()]


def chunk_recursive(text: str, size: int = 120) -> list[str]:
    """Pack paragraphs, then sentences, up to a token budget — respects structure."""
    chunks: list[str] = []
    for para in [p for p in text.split("\n\n") if p.strip()]:
        if n_tokens(para) <= size:
            chunks.append(para.strip())
            continue
        cur = ""
        for sent in split_sentences(para):
            if n_tokens(cur + " " + sent) > size and cur:
                chunks.append(cur.strip())
                cur = sent
            else:
                cur = (cur + " " + sent).strip()
        if cur:
            chunks.append(cur.strip())
    return chunks


def chunk_semantic(text: str, threshold: float = 0.55, max_tokens: int = 160) -> list[str]:
    """Start a new chunk when consecutive sentences become dissimilar (topic shift)."""
    sents = split_sentences(text)
    if not sents:
        return []
    vecs = np.array(embed_texts(sents), dtype=np.float32)
    vecs /= np.clip(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-12, None)

    chunks, cur = [], [sents[0]]
    for i in range(1, len(sents)):
        sim = float(vecs[i] @ vecs[i - 1])
        too_big = n_tokens(" ".join(cur + [sents[i]])) > max_tokens
        if sim < threshold or too_big:
            chunks.append(" ".join(cur))
            cur = [sents[i]]
        else:
            cur.append(sents[i])
    chunks.append(" ".join(cur))
    return chunks


STRATEGIES = {
    "fixed": lambda t: chunk_fixed(t, 120, 0),
    "overlap": lambda t: chunk_overlap(t, 120, 24),
    "recursive": lambda t: chunk_recursive(t, 120),
    "semantic": lambda t: chunk_semantic(t, 0.55, 160),
}


# ----------------------------- retrieval probe -----------------------------
def best_chunk(query: str, chunks: list[str]):
    cv = np.array(embed_texts(chunks), dtype=np.float32)
    cv /= np.clip(np.linalg.norm(cv, axis=1, keepdims=True), 1e-12, None)
    q = np.array(embed_query(query), dtype=np.float32)
    q /= np.clip(np.linalg.norm(q), 1e-12, None)
    scores = cv @ q
    i = int(np.argmax(scores))
    return float(scores[i]), chunks[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default=None)
    args = ap.parse_args()

    text = open(DOC, encoding="utf-8").read()
    queries = [args.query] if args.query else [
        "What does Orbit do when a host gets too hot?",
        "How long is the disaster recovery RPO and RTO?",
        "What happens to messages that keep failing in Relay?",
    ]

    # show how many chunks each strategy produces
    print("Chunk counts per strategy:")
    chunked = {}
    for name, fn in STRATEGIES.items():
        chunked[name] = fn(text)
        sizes = [n_tokens(c) for c in chunked[name]]
        print(f"  {name:10s}: {len(chunked[name]):3d} chunks | tokens min/avg/max = "
              f"{min(sizes)}/{sum(sizes)//len(sizes)}/{max(sizes)}")
    print()

    for q in queries:
        print("=" * 78)
        print(f"QUERY: {q}\n")
        for name in STRATEGIES:
            score, chunk = best_chunk(q, chunked[name])
            preview = chunk[:160].replace("\n", " ")
            print(f"  {name:10s} top score {score:.3f} | {preview}...")
        print()
    print("Notice: the strategy that isolates the right idea cleanly tends to win. "
          "There is no universal best — measure on YOUR docs (project 05).")


if __name__ == "__main__":
    main()
