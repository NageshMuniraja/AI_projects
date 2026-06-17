"""Project 07 — Graph RAG: extract a knowledge graph, then answer multi-hop questions
that pure vector search struggles with (doc 10).

Pipeline:
  1. EXTRACT (subject, relation, object) triples from the document with an LLM.
  2. BUILD an in-memory knowledge graph with NetworkX.
  3. RETRIEVE by locating entry entities in the question and traversing edges (multi-hop).
  4. COMPARE against plain vector RAG on the same question to SEE graph win.

Run:
    python graph_rag.py
    python graph_rag.py "Who reports to the person who owns the billing service?"
    python graph_rag.py --show-graph
"""
from __future__ import annotations

import os
import re
import sys

import networkx as nx
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.embeddings import embed_query, embed_texts  # noqa: E402
from common.llm import chat  # noqa: E402

DOC = os.path.join(os.path.dirname(__file__), "data", "org.md")


# ----------------------------- 1. extract triples -----------------------------
EXTRACT_SYSTEM = (
    "Extract knowledge-graph triples from the text. Output one triple per line as:\n"
    "subject | relation | object\n"
    "Use short canonical relations like: reports_to, owns, depends_on, role, on_call_for.\n"
    "Use full proper names for people and services. Output ONLY the triples."
)


def extract_triples(text: str):
    out = chat(EXTRACT_SYSTEM, text, max_tokens=1200)
    triples = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 3 and all(parts):
            triples.append(tuple(parts))
    return triples


# ----------------------------- 2. build graph -----------------------------
def build_graph(triples):
    g = nx.DiGraph()
    for s, r, o in triples:
        g.add_edge(s, o, relation=r)
    return g


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def find_entities(question: str, graph):
    """Match graph nodes that appear (loosely) in the question."""
    qn = norm(question)
    hits = []
    for node in graph.nodes:
        n = norm(node)
        # match on full node text or on a distinctive word (e.g., 'billing', 'ledger')
        if n and (n in qn or any(w in qn for w in n.split() if len(w) > 3)):
            hits.append(node)
    return hits


# ----------------------------- 3. graph retrieval -----------------------------
def subgraph_facts(graph, seeds, hops=2):
    """Collect edges within `hops` of any seed node, as readable 'A --relation--> B' facts."""
    nodes = set(seeds)
    frontier = set(seeds)
    for _ in range(hops):
        nxt = set()
        for n in frontier:
            nxt |= set(graph.successors(n)) | set(graph.predecessors(n))
        nodes |= nxt
        frontier = nxt
    facts = []
    for u, v, d in graph.edges(data=True):
        if u in nodes or v in nodes:
            facts.append(f"{u} --{d['relation']}--> {v}")
    return sorted(set(facts))


def graph_answer(question, graph):
    seeds = find_entities(question, graph)
    facts = subgraph_facts(graph, seeds) if seeds else []
    if not facts:
        return "No relevant entities found in the graph.", facts
    ans = chat(
        "Answer the question using ONLY these graph facts (A --relation--> B). "
        "Reason step by step across multiple facts if needed. Be concise.",
        "FACTS:\n" + "\n".join(facts) + f"\n\nQUESTION: {question}\nANSWER:",
    )
    return ans, facts


# ----------------------------- 4. vector RAG (for comparison) -----------------------------
def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) > 15]


def vector_answer(question, sents, vecs):
    qv = np.array(embed_query(question), dtype=np.float32)
    qv /= np.clip(np.linalg.norm(qv), 1e-12, None)
    idx = np.argsort(vecs @ qv)[::-1][:3]
    ctx = [sents[i] for i in idx]
    ans = chat(
        'Answer using ONLY the context. If not present, say you don\'t have enough information.',
        "CONTEXT:\n" + "\n".join(ctx) + f"\n\nQUESTION: {question}\nANSWER:",
    )
    return ans, ctx


def main():
    show_graph = "--show-graph" in sys.argv
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]

    text = open(DOC, encoding="utf-8").read()
    print("Extracting triples with the LLM...")
    triples = extract_triples(text)
    graph = build_graph(triples)
    print(f"Built graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.\n")

    if show_graph:
        for u, v, d in sorted(graph.edges(data=True)):
            print(f"  {u} --{d['relation']}--> {v}")
        print()

    sents = sentences(text)
    vecs = np.array(embed_texts(sents), dtype=np.float32)
    vecs /= np.clip(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-12, None)

    queries = argv and [" ".join(argv)] or [
        "Who reports to the person who owns the billing service?",   # multi-hop: billing->Sol->Lena->reports
        "What does Helios Pipe depend on, and who owns it?",          # 2-hop
    ]

    for q in queries:
        print("=" * 80)
        print(f"QUESTION: {q}\n")
        g_ans, facts = graph_answer(q, graph)
        v_ans, _ = vector_answer(q, sents, vecs)
        print(f"  GRAPH RAG : {g_ans}")
        print(f"      (facts used: {len(facts)})")
        print(f"  VECTOR RAG: {v_ans}\n")

    print("Multi-hop questions usually favor graph traversal: vector search finds similar "
          "sentences but can't reliably CHAIN facts across them. (doc 10)")


if __name__ == "__main__":
    main()
