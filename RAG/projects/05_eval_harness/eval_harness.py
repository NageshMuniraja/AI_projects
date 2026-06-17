"""Project 05 — Evaluation harness (the senior skill).

Compares two retrieval pipelines on a golden dataset and scores them on the four core
RAG metrics: faithfulness, answer relevancy, context precision, context recall (doc 07).

Two scoring backends:
  --judge ragas   : use the RAGAS library (pip install ragas)
  --judge custom  : a transparent LLM-as-judge built from scratch (default; always runs)

Run:
    python eval_harness.py                       # custom judge, both pipelines
    python eval_harness.py --pipeline hybrid
    python eval_harness.py --judge ragas

The point: change ONE thing (chunking, retriever, prompt), re-run, and SEE the numbers move.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np
from rank_bm25 import BM25Okapi

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.embeddings import embed_query, embed_texts  # noqa: E402
from common.llm import chat  # noqa: E402

HERE = os.path.dirname(__file__)
KB = os.path.join(HERE, "data", "kb.md")
GOLDEN = os.path.join(HERE, "golden.json")

GEN_SYSTEM = (
    "Answer using ONLY the context. If the answer is not present, reply exactly: "
    '"I don\'t have enough information in the provided documents to answer that." '
    "Be concise."
)


# ----------------------------- corpus + retrieval -----------------------------
def load_passages(path: str) -> list[str]:
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"\n##\s+", text)
    out = []
    for p in parts[1:]:
        lines = p.strip().splitlines()
        out.append(f"{lines[0].strip()}. " + " ".join(l.strip() for l in lines[1:]))
    return out


def tokenize(s: str) -> list[str]:
    return re.findall(r"[a-z0-9\-]+", s.lower())


class Retriever:
    def __init__(self, passages):
        self.passages = passages
        self.vecs = np.array(embed_texts(passages), dtype=np.float32)
        self.vecs /= np.clip(np.linalg.norm(self.vecs, axis=1, keepdims=True), 1e-12, None)
        self.bm25 = BM25Okapi([tokenize(p) for p in passages])

    def naive(self, q, k=3):
        qv = np.array(embed_query(q), dtype=np.float32)
        qv /= np.clip(np.linalg.norm(qv), 1e-12, None)
        idx = np.argsort(self.vecs @ qv)[::-1][:k]
        return [self.passages[i] for i in idx]

    def hybrid(self, q, k=3, cand=6):
        qv = np.array(embed_query(q), dtype=np.float32)
        qv /= np.clip(np.linalg.norm(qv), 1e-12, None)
        v = list(np.argsort(self.vecs @ qv)[::-1][:cand])
        b = list(np.argsort(self.bm25.get_scores(tokenize(q)))[::-1][:cand])
        scores = {}
        for ranked in (v, b):
            for r, i in enumerate(ranked):
                scores[i] = scores.get(i, 0.0) + 1.0 / (60 + r)
        top = sorted(scores, key=scores.get, reverse=True)[:k]
        return [self.passages[i] for i in top]


def generate(question, contexts):
    ctx = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    return chat(GEN_SYSTEM, f"CONTEXT:\n{ctx}\n\nQUESTION:\n{question}\n\nANSWER:")


# ----------------------------- custom LLM judge -----------------------------
def _ask_score(prompt: str) -> float:
    """Ask the judge for a single number in [0,1]."""
    out = chat("You are a strict evaluator. Reply with ONLY a number between 0 and 1.", prompt)
    m = re.search(r"[01](?:\.\d+)?", out)
    return float(m.group()) if m else 0.0


def judge_custom(question, answer, contexts, ground_truth):
    ctx = "\n".join(contexts)
    faith = _ask_score(
        f"Context:\n{ctx}\n\nAnswer:\n{answer}\n\n"
        "What fraction of the claims in the Answer are directly supported by the Context? "
        "1.0 = fully supported, 0.0 = unsupported/hallucinated."
    )
    rel = _ask_score(
        f"Question:\n{question}\n\nAnswer:\n{answer}\n\n"
        "How well does the Answer address the Question? 1.0 = perfectly, 0.0 = not at all."
    )
    prec = _ask_score(
        f"Question:\n{question}\n\nRetrieved context:\n{ctx}\n\n"
        "What fraction of the retrieved context is relevant to answering the question? "
        "1.0 = all relevant, 0.0 = all irrelevant."
    )
    rec = _ask_score(
        f"Reference answer:\n{ground_truth}\n\nRetrieved context:\n{ctx}\n\n"
        "Does the retrieved context contain the information needed to produce the reference answer? "
        "1.0 = fully present, 0.0 = absent."
    )
    return {"faithfulness": faith, "answer_relevancy": rel, "context_precision": prec, "context_recall": rec}


# ----------------------------- ragas backend -----------------------------
def judge_ragas(rows):
    """rows: list of dict(question, answer, contexts, ground_truth). Returns averaged metrics."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    ds = Dataset.from_list(
        [
            {
                "question": r["question"],
                "answer": r["answer"],
                "contexts": r["contexts"],
                "ground_truth": r["ground_truth"],
            }
            for r in rows
        ]
    )
    result = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision, context_recall])
    df = result.to_pandas()
    return {m: float(df[m].mean()) for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]}


# ----------------------------- run -----------------------------
def run_pipeline(name, retriever, golden, judge):
    rows = []
    per_metric = {"faithfulness": [], "answer_relevancy": [], "context_precision": [], "context_recall": []}
    print(f"\n--- pipeline: {name} ---")
    for item in golden:
        q, gt = item["question"], item["ground_truth"]
        contexts = retriever.naive(q) if name == "naive" else retriever.hybrid(q)
        ans = generate(q, contexts)
        rows.append({"question": q, "answer": ans, "contexts": contexts, "ground_truth": gt})
        if judge == "custom":
            scores = judge_custom(q, ans, contexts, gt)
            for k, v in scores.items():
                per_metric[k].append(v)
            print(f"  Q: {q[:48]:48s} faith={scores['faithfulness']:.2f} "
                  f"rel={scores['answer_relevancy']:.2f} prec={scores['context_precision']:.2f} "
                  f"rec={scores['context_recall']:.2f}")
    if judge == "ragas":
        return judge_ragas(rows)
    return {k: (sum(v) / len(v) if v else 0.0) for k, v in per_metric.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", choices=["naive", "hybrid", "both"], default="both")
    ap.add_argument("--judge", choices=["custom", "ragas"], default="custom")
    args = ap.parse_args()

    passages = load_passages(KB)
    golden = json.load(open(GOLDEN))
    retriever = Retriever(passages)

    names = ["naive", "hybrid"] if args.pipeline == "both" else [args.pipeline]
    results = {n: run_pipeline(n, retriever, golden, args.judge) for n in names}

    print("\n" + "=" * 72)
    print(f"RESULTS (judge={args.judge})  — higher is better, max 1.0")
    print(f"{'metric':22s} " + " ".join(f"{n:>10s}" for n in names))
    for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        print(f"{metric:22s} " + " ".join(f"{results[n][metric]:10.3f}" for n in names))
    print("=" * 72)
    if len(names) == 2:
        print("If hybrid > naive on precision/recall, you've PROVEN your retrieval change helped. (doc 07)")


if __name__ == "__main__":
    main()
