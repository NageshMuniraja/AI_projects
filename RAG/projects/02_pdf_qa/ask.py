"""Project 02 — Ask questions against the ingested PDFs (with citations + optional filtering).

Run:
    python ask.py "How long is the free trial?"
    python ask.py "What is the uptime SLA?" --k 5
    python ask.py "What regions are supported?" --source helios_policies.pdf   # metadata filter

Make sure you ran ingest.py first.
"""
from __future__ import annotations

import argparse
import os
import sys

import chromadb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.embeddings import embed_query  # noqa: E402
from common.llm import chat  # noqa: E402

HERE = os.path.dirname(__file__)
CHROMA_DIR = os.path.join(HERE, ".chroma")
COLLECTION = "pdf_qa"

SYSTEM_PROMPT = (
    "You answer strictly from the provided context. Rules:\n"
    "- Use ONLY the context. If the answer is not present, reply exactly: "
    '"I don\'t have enough information in the provided documents to answer that."\n'
    "- Cite every claim with its source marker like (helios_policies.pdf, p.3).\n"
    "- Be concise and do not speculate."
)


def search(query: str, k: int, source: str | None):
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_collection(COLLECTION)
    where = {"source": source} if source else None
    res = col.query(
        query_embeddings=[embed_query(query)],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        # chroma cosine distance -> similarity
        hits.append({"text": doc, "meta": meta, "score": 1 - dist})
    return hits


def build_context(hits) -> str:
    lines = []
    for h in hits:
        tag = f"({h['meta']['source']}, p.{h['meta']['page']})"
        lines.append(f"{tag} {h['text']}")
    return "\n\n".join(lines)


def answer(query: str, k: int = 4, source: str | None = None, min_score: float = 0.20):
    hits = search(query, k, source)
    if not hits or hits[0]["score"] < min_score:
        return "I don't have enough information in the provided documents to answer that.", hits
    context = build_context(hits)
    user = f"CONTEXT:\n{context}\n\nQUESTION:\n{query}\n\nANSWER (with source citations):"
    return chat(SYSTEM_PROMPT, user), hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--source", default=None, help="restrict to one PDF filename (metadata filter)")
    args = ap.parse_args()

    q = " ".join(args.question)
    ans, hits = answer(q, k=args.k, source=args.source)
    print(f"Q: {q}\n")
    print(f"A: {ans}\n")
    print("Sources used:")
    for h in hits:
        print(f"  ({h['meta']['source']}, p.{h['meta']['page']})  score={h['score']:.3f}  {h['text'][:70]!r}...")


if __name__ == "__main__":
    main()
