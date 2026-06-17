"""Project 01 — Hello RAG (from scratch, no framework).

Goal: see every moving part of RAG with nothing hidden. We will:
  1. LOAD a text file
  2. CHUNK it (fixed size + overlap)
  3. EMBED each chunk (OpenAI)
  4. RETRIEVE the top-k chunks for a question (cosine similarity, computed by hand)
  5. GENERATE a grounded, cited answer (and refuse when the answer isn't in the docs)

Run:
    python hello_rag.py                      # answers a few demo questions
    python hello_rag.py "your question?"     # ask your own

Read docs/01_rag_fundamentals.md and docs/02_embeddings_and_vectors.md alongside this.
"""
from __future__ import annotations

import os
import sys

import numpy as np

# --- make the shared helpers in common/ importable from this subfolder ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.embeddings import embed_query, embed_texts  # noqa: E402
from common.llm import chat  # noqa: E402

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "helios_handbook.txt")

SYSTEM_PROMPT = (
    "You are a precise assistant. Answer the question using ONLY the context provided.\n"
    "- If the answer is not in the context, reply exactly: "
    '"I don\'t have enough information in the provided documents to answer that."\n'
    "- Cite the chunk number(s) you used like [1], [2].\n"
    "- Be concise. Do not use outside knowledge or guess."
)


# ----------------------------- 1 & 2. load + chunk -----------------------------
def load_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """Fixed-size character chunking with overlap (the simplest sane strategy).

    chunk_size/overlap are in CHARACTERS here for clarity. Real systems usually
    count tokens — you'll do that in later projects. Try changing these and see
    how retrieval changes (that's the whole point of doc 03).
    """
    chunks, start = [], 0
    text = text.strip()
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap  # step back by `overlap` so chunks overlap
    return [c for c in chunks if c]


# ----------------------------- 3. embed (index) -----------------------------
def build_index(chunks: list[str]) -> np.ndarray:
    """Return an (n_chunks x dim) matrix of L2-normalized embeddings.

    Normalizing once means cosine similarity == a single dot product later (fast).
    """
    vecs = np.array(embed_texts(chunks), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / np.clip(norms, 1e-12, None)


# ----------------------------- 4. retrieve -----------------------------
def retrieve(query: str, chunks: list[str], index: np.ndarray, k: int = 3):
    """Return the top-k (score, chunk_index, chunk_text) by cosine similarity."""
    q = np.array(embed_query(query), dtype=np.float32)
    q = q / np.clip(np.linalg.norm(q), 1e-12, None)
    scores = index @ q  # cosine similarity for every chunk at once
    top = np.argsort(scores)[::-1][:k]
    return [(float(scores[i]), int(i), chunks[i]) for i in top]


# ----------------------------- 5. generate -----------------------------
def answer(query: str, chunks: list[str], index: np.ndarray, k: int = 3, min_score: float = 0.20):
    hits = retrieve(query, chunks, index, k=k)

    # Relevance gate: if even the best chunk is weak, refuse instead of guessing.
    if not hits or hits[0][0] < min_score:
        return (
            "I don't have enough information in the provided documents to answer that.",
            hits,
        )

    context = "\n\n".join(f"[{rank+1}] {text}" for rank, (_, _, text) in enumerate(hits))
    user = f"CONTEXT:\n{context}\n\nQUESTION:\n{query}\n\nANSWER (cite with [n]):"
    return chat(SYSTEM_PROMPT, user), hits


def main():
    print("Loading + chunking + embedding (first run embeds; later runs use the cache)...")
    text = load_text(DATA_FILE)
    chunks = chunk_text(text)
    index = build_index(chunks)
    print(f"Indexed {len(chunks)} chunks.\n")

    if len(sys.argv) > 1:
        questions = [" ".join(sys.argv[1:])]
    else:
        questions = [
            "How long is the free trial and do I need a credit card?",      # answerable
            "What credit do I get if uptime drops to 98.5 percent?",         # answerable (needs the SLA chunk)
            "Can I pay with Dogecoin?",                                      # NOT in the docs -> should refuse
        ]

    for q in questions:
        ans, hits = answer(q, chunks, index)
        print("=" * 70)
        print(f"Q: {q}")
        print(f"A: {ans}")
        print("\nRetrieved chunks (score | preview):")
        for score, idx, text in hits:
            print(f"  [{idx}] {score:.3f} | {text[:80].replace(chr(10), ' ')}...")
        print()


if __name__ == "__main__":
    main()
