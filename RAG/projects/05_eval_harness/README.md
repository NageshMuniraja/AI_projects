# Project 05 — Evaluation Harness (RAGAS)

**Level:** Intermediate+ · **Day:** 7 · **Read first:** `docs/07_evaluation_ragas.md`

This is the project that makes you senior. Until now you judged answers by eye. Here you put a **number** on every component and use it to *prove* a change helped. You evaluate two pipelines (naive vector vs hybrid) on a **golden dataset** across the four core metrics.

## Run it

```bash
cd projects/05_eval_harness
python eval_harness.py                  # custom LLM-judge (always works), both pipelines
python eval_harness.py --judge ragas    # use the RAGAS library instead
python eval_harness.py --pipeline hybrid
```

Output is a table comparing **naive** vs **hybrid** on faithfulness, answer relevancy, context precision, and context recall.

> Note: evaluation calls the LLM many times (it's LLM-as-judge), so this is the most token-heavy project. With `gpt-4o-mini` it's still cents.

## Two scoring backends

- **`--judge custom` (default):** a transparent LLM-as-judge written from scratch in `eval_harness.py` (`judge_custom`). You can read exactly how each metric is computed — great for understanding. Always runs.
- **`--judge ragas`:** uses the real [RAGAS](https://docs.ragas.io) library. Industry-standard; what you'd cite in an interview. If your installed RAGAS version's API differs, the custom judge still has you covered.

## The four metrics (and what a low score means)

| Metric | Measures | Low → fix |
|---|---|---|
| **faithfulness** | answer supported by context (anti-hallucination) | tighten grounding prompt / relevance gate (Doc 06) |
| **answer_relevancy** | answer addresses the question | prompt/format; clarify ambiguous Qs |
| **context_precision** | retrieved chunks are relevant & well-ranked | add reranking / hybrid / filters (Doc 05) |
| **context_recall** | retrieval fetched all needed info | chunking / higher top-k (Doc 03) |

This precision/recall vs faithfulness/relevancy split tells you **whether to fix retrieval or generation** — the key senior debugging move.

## The golden dataset

`golden.json` holds 10 reviewed `(question, ground_truth)` pairs — including an **out-of-scope** one ("Can I pay with Dogecoin?") to test that the system *refuses* instead of hallucinating. Real golden sets have 30–50+; this is a teaching-sized sample.

## Stretch goals (this is the engine for the rest of the course)

1. **Prove hybrid beats naive.** Run both and confirm hybrid lifts context precision/recall. That's the Day-7 milestone.
2. **One variable at a time.** Change top-k, then chunking, then the prompt — re-run after each, keep only what improves the metric you targeted without hurting others.
3. **Grow the dataset.** Add 10 of your own questions (easy, multi-hop, out-of-scope). Watch the numbers get more trustworthy.
4. **Compare judges.** Run `--judge custom` and `--judge ragas` on the same pipeline; discuss why scores differ.
5. **Catch a regression.** Deliberately break the prompt (remove the grounding rule) and watch faithfulness fall — this is what CI eval (Day 13) guards against.
6. **Bring your Project 03/04 work here.** Score the chunking strategy and the rerank step you built, and let the numbers pick the winner.

## Concepts made concrete

- All four RAGAS metrics and LLM-as-judge (Doc 07)
- Retrieval-vs-generation failure diagnosis
- The measure → change one thing → re-measure loop that drives Week 2
