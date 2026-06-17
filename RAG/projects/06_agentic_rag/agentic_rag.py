"""Project 06 — Agentic RAG: adaptive routing + multi-step retrieval + tools.

Built from scratch so the agent loop is fully visible (no framework magic). It shows the
two highest-value agentic patterns from doc 09:
  1. ROUTING (Adaptive RAG): classify each query and send it down the cheapest path that works.
  2. MULTI-STEP retrieval: decompose a complex query, retrieve per sub-question, synthesize.
Plus a TOOL (calculator) and a max-step budget so the loop can't run away.

Run:
    python agentic_rag.py
    python agentic_rag.py "hi there"                              # -> no_retrieval path
    python agentic_rag.py "what is 4999 * 12 for annual premium?" # -> tool path
    python agentic_rag.py "Compare the cost and response time of Standard vs Premium support"  # multi-hop
"""
from __future__ import annotations

import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.embeddings import embed_query, embed_texts  # noqa: E402
from common.llm import chat  # noqa: E402

KB = os.path.join(os.path.dirname(__file__), "data", "kb.md")
MAX_STEPS = 4  # budget: never loop more than this many sub-questions


# ----------------------------- retrieval (tool #1) -----------------------------
def load_passages(path):
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"\n##\s+", text)
    return [f"{p.strip().splitlines()[0].strip()}. " + " ".join(l.strip() for l in p.strip().splitlines()[1:])
            for p in parts[1:]]


PASSAGES = load_passages(KB)
_VECS = np.array(embed_texts(PASSAGES), dtype=np.float32)
_VECS /= np.clip(np.linalg.norm(_VECS, axis=1, keepdims=True), 1e-12, None)


def retrieve(query, k=3):
    qv = np.array(embed_query(query), dtype=np.float32)
    qv /= np.clip(np.linalg.norm(qv), 1e-12, None)
    idx = np.argsort(_VECS @ qv)[::-1][:k]
    return [PASSAGES[i] for i in idx]


# ----------------------------- calculator (tool #2) -----------------------------
def calculator(expr: str) -> str:
    """Safe arithmetic only (digits and + - * / . ( ) )."""
    if not re.fullmatch(r"[\d\s+\-*/().]+", expr):
        return "ERROR: unsupported expression"
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 - sanitized above
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {e}"


# ----------------------------- router -----------------------------
ROUTE_SYSTEM = (
    "Classify the user query into exactly one route. Reply with ONLY the label.\n"
    "- no_retrieval : greetings, chit-chat, or general knowledge not about Helios docs\n"
    "- tool         : the query needs arithmetic/calculation\n"
    "- simple       : a single fact lookup answerable from one place in the docs\n"
    "- multi_hop    : needs several facts combined, comparisons, or multiple lookups"
)


def route(query: str) -> str:
    label = chat(ROUTE_SYSTEM, f"Query: {query}\nRoute:").strip().lower()
    for r in ("no_retrieval", "multi_hop", "simple", "tool"):
        if r in label:
            return r
    return "simple"


# ----------------------------- answer paths -----------------------------
GROUND = ('Answer using ONLY the context. If not present, say you don\'t have enough '
          "information in the documents. Be concise and cite with [n].")


def answer_simple(query):
    ctx = retrieve(query)
    body = "\n".join(f"[{i+1}] {c}" for i, c in enumerate(ctx))
    return chat(GROUND, f"CONTEXT:\n{body}\n\nQUESTION: {query}\nANSWER:"), ctx


def answer_no_retrieval(query):
    return chat("You are a concise, friendly assistant.", query), []


def answer_tool(query):
    expr = chat(
        "Extract ONLY the arithmetic expression to evaluate from the user's request. "
        "Reply with just the expression (digits and + - * / ( ) ), nothing else.",
        query,
    ).strip()
    result = calculator(expr)
    final = chat("You are concise.", f"The user asked: {query}\nComputed {expr} = {result}. "
                                     "Give a one-sentence answer.")
    return final, [f"calculator: {expr} = {result}"]


def decompose(query):
    out = chat(
        "Break the user's question into 2-4 minimal sub-questions, each answerable by a single "
        "document lookup. Reply as a numbered list, one sub-question per line.",
        query,
    )
    subs = [re.sub(r"^\s*\d+[.)]\s*", "", ln).strip() for ln in out.splitlines() if ln.strip()]
    return subs[:MAX_STEPS]


def answer_multi_hop(query):
    subs = decompose(query)
    notes, used = [], []
    for i, sub in enumerate(subs, 1):
        ctx = retrieve(sub, k=2)
        used += ctx
        sub_ans = chat(GROUND, f"CONTEXT:\n" + "\n".join(ctx) + f"\n\nQUESTION: {sub}\nANSWER:")
        notes.append(f"Sub-Q{i}: {sub}\n  -> {sub_ans}")
        print(f"   step {i}: {sub}\n            {sub_ans[:90]}")
    synthesis = chat(
        "Synthesize a single, concise final answer from these sub-answers. Cite nothing you weren't told.",
        f"Original question: {query}\n\nSub-answers:\n" + "\n".join(notes) + "\n\nFinal answer:",
    )
    return synthesis, used


# ----------------------------- orchestrator -----------------------------
def agent(query: str):
    r = route(query)
    print(f"  → route: {r}")
    if r == "no_retrieval":
        return answer_no_retrieval(query)
    if r == "tool":
        return answer_tool(query)
    if r == "multi_hop":
        return answer_multi_hop(query)
    return answer_simple(query)


def main():
    queries = sys.argv[1:] and [" ".join(sys.argv[1:])] or [
        "hello, who are you?",                                              # no_retrieval
        "How long is the free trial?",                                      # simple
        "What is 499 * 12 if I prepay Premium support for a year?",         # tool
        "Compare the price and response time of Standard vs Premium support",  # multi_hop
    ]
    for q in queries:
        print("=" * 78)
        print(f"USER: {q}")
        ans, _ = agent(q)
        print(f"ASSISTANT: {ans}\n")


if __name__ == "__main__":
    main()
