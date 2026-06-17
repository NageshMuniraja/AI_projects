"""Project 02 — Ingest PDFs into a persistent Chroma vector store.

Pipeline: load PDF (per page) -> token-chunk with overlap -> embed -> store in Chroma
with metadata (source filename + page) so we can cite and filter later.

Run:
    python ingest.py                 # ingests every PDF in ./data
    python ingest.py --reset         # wipe the collection and re-ingest

Then ask questions with:  python ask.py "..."
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import chromadb
import tiktoken
from pypdf import PdfReader

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.embeddings import embed_texts  # noqa: E402

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "data")
CHROMA_DIR = os.path.join(HERE, ".chroma")
COLLECTION = "pdf_qa"

_enc = tiktoken.get_encoding("cl100k_base")


def token_chunks(text: str, size: int = 350, overlap: int = 60) -> list[str]:
    """Chunk by TOKENS (not characters) — closer to how the LLM and limits actually count."""
    toks = _enc.encode(text)
    out, start = [], 0
    while start < len(toks):
        piece = toks[start : start + size]
        out.append(_enc.decode(piece).strip())
        start += size - overlap
    return [c for c in out if c.strip()]


def load_pdf_pages(path: str) -> list[tuple[int, str]]:
    """Return [(page_number, page_text), ...] (1-indexed pages)."""
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        txt = (page.extract_text() or "").strip()
        if txt:
            pages.append((i + 1, txt))
    return pages


def get_collection(reset: bool = False):
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    if reset:
        try:
            client.delete_collection(COLLECTION)
        except Exception:  # noqa: BLE001
            pass
    # cosine space; we supply our own embeddings so no embedding_function needed
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="wipe collection before ingesting")
    args = ap.parse_args()

    pdfs = sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf")))
    if not pdfs:
        print(f"No PDFs found in {DATA_DIR}. Drop a .pdf there (a sample is included) and retry.")
        return

    col = get_collection(reset=args.reset)

    ids, docs, metas = [], [], []
    for path in pdfs:
        fname = os.path.basename(path)
        for page_no, page_text in load_pdf_pages(path):
            for j, chunk in enumerate(token_chunks(page_text)):
                ids.append(f"{fname}:p{page_no}:c{j}")  # stable id -> idempotent re-ingest
                docs.append(chunk)
                metas.append({"source": fname, "page": page_no})

    print(f"Embedding {len(docs)} chunks from {len(pdfs)} PDF(s)...")
    embeddings = embed_texts(docs)

    # upsert so re-running doesn't create duplicates
    col.upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)
    print(f"Done. Collection '{COLLECTION}' now holds {col.count()} chunks at {CHROMA_DIR}")
    print("Ask something:  python ask.py \"How long is the free trial?\"")


if __name__ == "__main__":
    main()
