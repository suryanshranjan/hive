# Gate 119: predictions (registered before launch, Nov 15 2026)

**Question.** Do the fixes for Gate 118's gaps close them on cases they were not tuned on? The fixes are:
- meaning-based recall (`hive/embed.py`, fastembed's bge-small, optional);
- one REMEMBER call that sees the related facts already kept and names the ones the new fact replaces (`assistant._related`, `keep`, `supersede`).

**Disclosure.** While building the meaning search I ran Gate 118's own R1 and R2 as a development check: R1 30/30, R2 5/6 (Gate 118 had 3/6). Those six questions are therefore not evidence for it. This gate uses new questions and new changes, written into `lab/memory_bench.py` (`HELDOUT`, `LIVE2`, `CONTROLS2_AFTER`) before any of them ran.

**H, held-out paraphrases** (`python lab/memory_bench.py heldout`, no LLM):
- Gate 118's 30 facts, plus 60 ordinary notes.
- 12 new questions that share no content word with their fact ("who handles our tax returns?" for Neha filing the GST).
- Arm `words` has embeddings off; arm `meaning` has them on.

**L, changes of mind** (`python lab/memory_bench.py live2`, the real model on the small tier):
- 6 facts, each changed later. 4 of the 6 are about how the business works (cancellations, late-delivery offer, corporate minimum, referrals), the kind Gate 118 lost.
- 4 control facts, never changed.
- 4 more messages on the same topics that change nothing.
- **Scored from the store:** is the old fact replaced, is the control still live. Not from keywords, which Gate 118 showed to be misleading.

| # | Prediction | Kill |
|---|---|---|
| H1 | `meaning` ≥ 9/12; `words` ≤ 4/12 | `meaning` < 7/12 |
| H2 | R1 (the 30 word-sharing questions) stays ≥ 29/30 with `meaning` (embeddings add, they don't crowd out) | < 27/30 |
| H3 | A recall with the model loaded takes ≤ 300 ms on this laptop (90 facts) | > 1,000 ms |
| L1 | All 10 first messages kept, and all 6 changes of mind kept, including the 4 about how the business works | < 8/10 first, or < 5/6 changes |
| L2 | The old fact is replaced for ≥ 5/6 changes (store-based) | < 4/6 |
| L3 | No control fact is replaced by the same-topic messages: ≥ 4/4 still live | < 3/4 |
| L4 | The current answer is in the context recall gives, for ≥ 9/10 questions | < 8/10 |
| L5 | Under $1 for the whole live run (one small-model call per message now, plus the numbers call when a message has digits) | > $3 |

**Confounds:**
- One business, written by me.
- One live run.
- The held-out questions were written knowing the facts, though not knowing how the model would score them.
