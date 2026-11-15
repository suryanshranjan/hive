# Gate 118: predictions (registered before launch, Nov 15 2026)

**Question.** Does memory 2.0 (`hive/store.py`, `hive/recall.py`) put the right fact in front of a reply, where Hive's memory before it (his 15 newest notes, whatever he asked) did not? And does a change of mind replace the old fact without touching facts that only share its topic?

**The bench.** `lab/memory_bench.py`, with a fixed seed (118). It uses a mock business, "Dabba Days" (a tiffin service), with mock names only.
- **R1 (no model):** 30 facts among 90 ordinary notes, spread over 8 simulated weeks. Each fact gets one question that shares a word or two with it. A hit means the answer's keyword is in the context a reply is given.
  - Arm `last15` is the old behaviour (`memory.notes(repo)[-15:]`).
  - Arm `recall` is memory 2.0.
- **R2 (no model):** 6 questions that share no word with their fact.
- **R3 (live, the real model through `explain.ask_json`):** 16 of his messages go through the real REMEMBER and REPLACES prompts.
  - 8 of the facts are later changed ("we moved to Gupta Foods for dal").
  - 8 are controls.
  - 8 more messages touch the same topics without changing anything.
  - Scored from the context `recall` gives each question.

| # | Prediction | Kill |
|---|---|---|
| M1 | R1: `recall` hits ≥ 26/30 (87%). `last15` ≤ 6/30 (about the share of facts that happen to be among the newest 15 notes). | `recall` < 21/30 |
| M2 | R1: a reply is never given more than 12 facts. | > 12 |
| M3 | R2: `recall` ≤ 3/6. Keyword search cannot bridge "lentils" to "dal". This limit is expected and is the case for embeddings (optional `fastembed`) in a later step. | none (measured, to decide on embeddings) |
| M4 | R3: ≥ 15 of the 16 first messages are kept as lasting facts. | < 12 |
| M5 | R3: after the 8 changes of mind, the new value is recalled for ≥ 7/8, and the old value is gone from the context for ≥ 6/8. | old value gone < 4/8 |
| M6 | R3: the 8 controls are all still recalled after the same-topic messages (no false replacement): ≥ 7/8. | < 6/8 |
| M7 | R3: Asha's facts are linked to her as a person. | not linked |
| M8 | R3 costs under $2 of Hive's own model calls. | > $5 |

**Confounds, stated now:**
- The questions are mine, written alongside the facts, so R1's word overlap is friendlier than a real founder's questions; R2 is there to show the other side.
- There is one business and one seed.
- R3 is a single run with one model; τ-bench-style repeats come later if it is close.
