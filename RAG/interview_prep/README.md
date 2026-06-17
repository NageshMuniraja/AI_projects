# Interview Prep

Everything to prepare for an AI Engineer / RAG Architect interview, in increasing depth.

| File | What it is | When to use |
|---|---|---|
| `01_question_bank.md` | 70+ Q&A, tagged 🟢 Junior / 🟡 Mid / 🔴 Architect, grouped by topic | A little each day (the 🎯 step in ROADMAP) |
| `02_system_design_playbook.md` | A 7-step design framework, 2 worked scenarios, and a mock interview | Day 14, and before any onsite |
| `03_cheatsheet.md` | One-page quick reference: defaults, numbers, trade-offs | Final review / day-of |
| `04_beginner_to_architect_qna.md` | 100 progressive Q&A from beginner fundamentals to architect design | Level-by-level speaking practice |
| **PDFs** | `RAG_Interview_Prep_Guide.pdf` (bank + playbook) and `RAG_Cheat_Sheet.pdf` | Print / read offline / phone review |

## How to use it

- **Daily (20–30 min):** read the question-bank section that matches the day's topic (mapping is in `ROADMAP.md`). Read the model answer, then close the doc and answer **out loud** in your own words.
- **Weekly:** do a timed pass of one system-design scenario from the playbook.
- **Day 14:** run the full mock interview, score yourself with the rubric, and record yourself defending three trade-offs.

## The one habit that gets you hired

For every senior/architect answer, pair a **trade-off** with a **number**:
> "I'd default to hybrid retrieval with reranking — it adds ~50–150ms but lifted context precision from 0.74 to 0.88 on our golden set, and I'd cache to claw the latency back."

That sentence shape — decision, trade-off, measured impact — is what separates someone who *uses* RAG from someone who can *own* it.
