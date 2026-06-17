# 07 · Evaluation with RAGAS

> Day 7. This is the chapter that turns you from "I built a RAG demo" into "I improve RAG systems." Seniors measure.

## Why evaluation is the whole job

RAG has many knobs (chunk size, embedding model, top-k, hybrid weights, reranker, prompt). You cannot tune them by eyeballing a few answers — you'll fool yourself. **Evaluation gives you a number for each component**, so you can change one thing, re-measure, and *know* whether it helped. Without it, you're guessing; with it, you're engineering.

## Separate the two failure domains

A wrong answer is either a **retrieval** problem or a **generation** problem. Good metrics tell you which:

```
              did we FETCH the right context?        did we USE it correctly?
              ───────────────────────────────        ─────────────────────────
   RETRIEVAL: context precision, context recall   |  GENERATION: faithfulness, answer relevancy
```

If retrieval metrics are bad → fix chunking/retrieval (Docs 03, 05). If retrieval is good but generation metrics are bad → fix the prompt/model (Doc 06). This decomposition is *the* senior debugging move.

## The four core RAGAS metrics

| Metric | Question it answers | Low score means | Needs ground truth? |
|---|---|---|---|
| **Faithfulness** | Is every claim in the answer supported by the retrieved context? | Hallucination — model invented something | No |
| **Answer relevancy** | Does the answer actually address the question? | Off-topic / rambling / partial answer | No |
| **Context precision** | Are the retrieved chunks relevant, and are the relevant ones ranked high? | Retrieval returns junk / good chunks buried | Uses question (+ optional GT) |
| **Context recall** | Did retrieval fetch *all* the info needed to answer? | Retrieval missed required chunks | Yes (ground-truth answer) |

How they're computed: RAGAS uses **LLM-as-judge** — it prompts an LLM to break the answer into claims and check each against the context (faithfulness), to generate questions the answer implies and compare to the real one (relevancy), etc. So evaluation itself costs LLM calls (budget for it).

Mental model of each failure:
- **Low faithfulness, high everything else** → your prompt isn't grounding; tighten it / add a relevance gate.
- **Low context recall** → chunks too small, wrong chunking, or top-k too low; you're not fetching the needed info.
- **Low context precision** → too much irrelevant retrieval; add reranking / hybrid / better filters.
- **Low answer relevancy** → prompt/format issue or the question was ambiguous.

## The golden dataset

To evaluate you need a **test set**: representative `(question, ground_truth_answer)` pairs for your corpus, ideally with the expected source. 30–50 good examples beat 5 cherry-picked ones.

How to build it:
- Hand-write questions real users would ask (include easy, hard, multi-hop, and **out-of-scope** ones).
- Optionally **generate** candidate Q&A from your documents with an LLM, then **review by hand** — never trust un-reviewed synthetic data as ground truth.
- Cover the edges: questions the docs *can't* answer (to test refusal), ambiguous questions, and questions needing multiple chunks.

`projects/05_eval_harness` ships a small golden set and the code to score your pipeline on it.

## The optimization loop (do this for the rest of the course)

```
1. Lock a golden dataset.
2. Measure the current pipeline → baseline numbers.
3. Change ONE thing (e.g., chunk 512→256, or add reranking).
4. Re-measure.
5. Keep it only if the metric you targeted improved without tanking others.
6. Repeat.
```

This is exactly how you'll justify, on Day 8, which advanced techniques are worth their cost — and how, on Day 7, you'll prove hybrid+rerank beats naive retrieval.

## Beyond RAGAS (know these exist)

- **LLM-as-judge (custom)**: write your own rubric ("is this answer correct, grounded, and well-cited? score 1–5") — flexible, used widely in 2026.
- **Retrieval IR metrics**: hit-rate@k, MRR, nDCG when you have labeled relevant chunks.
- **Answer-correctness / semantic similarity** vs ground truth.
- **Guardrail/safety evals**: toxicity, PII leakage, prompt-injection resistance.
- **Online evaluation**: sample real production traffic and score it continuously (Day 13) — offline tests drift from reality.
- **Human review**: still the gold standard for high-stakes domains; use it to validate your automated metrics.

## Pitfalls

- **Tiny test sets** → noisy, misleading numbers. Get to ~30+.
- **Judge model = generator model** → can be biased; consider a different/stronger judge.
- **Optimizing one metric** → context recall up but faithfulness down is a bad trade. Watch the whole vector.
- **No out-of-scope questions** → you never learn whether the system refuses or hallucinates on the unknown.
- **Eval only once** → wire it into CI so a "small" prompt tweak can't silently regress quality (Day 13).

## Interview soundbites

- "I split evaluation into retrieval (context precision/recall) and generation (faithfulness, answer relevancy) so I know which half to fix."
- "RAGAS uses LLM-as-judge; faithfulness and answer relevancy need no ground truth, context recall does."
- "I keep a reviewed golden set, change one variable at a time, and put eval in CI so quality can't silently regress."
- "Low recall → chunking/top-k; low precision → add reranking; low faithfulness → grounding prompt + relevance gate."

➡️ End of Week 1. Next week starts with `docs/08_advanced_rag.md`.
