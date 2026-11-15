# Gate 118: results (Nov 15 2026)

**Question.** Does memory 2.0 put the right fact in front of a reply where the old memory (his 15 newest notes) did not, and does a change of mind replace the old fact without touching facts that only share its topic?

## Runs

- **R1 and R2:** `lab/memory_bench.py retrieval`. No model, so the result is deterministic.
- **R3:** `lab/memory_bench.py live`, run three times.
  - **Attempt 1, a setup fault:** the bench pointed HOME at a temp folder, so Claude Code found no login and every call failed (0 kept, $0). Kept as `results_live_attempt1.json`. Not scored.
  - **Attempt 2, the registered run, scored below:** `results_live_attempt2.json`.
  - **Attempt 3, after fixes found in attempt 2:** `results_live.json`. Reported separately; it is a second arm, not a rescore.

## R1 and R2 (no model)

| # | Prediction | Result | |
|---|---|---|---|
| M1 | `recall` ≥ 26/30; `last15` ≤ 6/30 | **`recall` 30/30; `last15` 2/30** | Held |
| M2 | A reply never gets more than 12 facts | **12 at most** | Held |
| M3 | Paraphrase questions: `recall` ≤ 3/6 | **3/6** (`last15` 1/6) | Held. Keyword search cannot bridge "lentils" to "dal". |

## R3 (live, attempt 2: the registered run)

| # | Prediction | Result | |
|---|---|---|---|
| M4 | ≥ 15/16 first messages kept as lasting facts | **15/16** (the refunds message was not kept) | Held |
| M5 | New value recalled ≥ 7/8; old value gone from the context ≥ 6/8 | New **7/8**; old gone **5/8** | **Failed** on the old value (kill < 4 not fired) |
| M6 | Controls still recalled ≥ 7/8 | **8/8**, and nothing was falsely replaced | Held |
| M7 | Asha's facts linked to her | **Not linked**: "Asha" in the change of mind became a second person beside "Asha Mehta" | **Failed** |
| M8 | Under $2 | **$6.80** | **Kill fired** (> $5) |

**Why M5 failed: the measure, mostly.**
- In all 3 misses, the new fact names the old value itself: "switched from Sharma to Gupta Foods", "Ravi has left, Sameer is now the delivery lead", "no longer works with Ankit".
- A keyword check cannot tell "Ravi leads delivery" from "Ravi has left".
- Every old fact that had been kept was replaced. The 8th change concerned the refunds fact, which was never kept in the first place.
- Scored on what matters, whether the old fact is still live: 7 of 7.
- The registered measure stays failed. This measure should not be used again as it is.

## Found and fixed from attempt 2

1. **A person by first name became a second person.** `store.person_id('Asha')` now finds the one known "Asha Mehta" and adds "Asha" as another name.
2. **Notes showed twice.** A fact kept as a person, preference or deadline was imported again as a plain note from the JSON. `store.sync` now matches any kind.
3. **Cost.** The small reading jobs now run on the small model (`explain.ask_small`, `claude-haiku-5-5`, `HIVE_SMALL_MODEL`). These are: is this worth remembering, does it replace an older fact, and the numbers in a message.

## Attempt 3 (after the fixes; not the registered run)

- **Kept:** 16/16.
- **Changes of mind:** new value 8/8; old facts replaced 7 (the refunds change itself was not kept as a fact this time); strict old-keyword-gone 4/8, for the same reason as above.
- **Controls:** 8/8.
- **Asha:** linked.
- **Cost: $1.77.** $1.00 of it was the numbers call, still on the default model in that run; it has been moved to the small model since. That makes about $0.77 for the rest.

## What it changes in the product

- Replies get `recall` (memory 2.0), not the 15 newest notes. It found 30 of 30 facts, against 2 of 30.
- A changed fact replaces the old one. It is kept for the record and no longer comes back.
- Memory's reading calls run on the small model.
- **Next:**
  - Embeddings for paraphrases (R2: 3/6). The optional `fastembed` extra would close the "lentils"/"dal" gap.
  - A follow-up when a change of mind is not kept: the refunds change was lost once in each live attempt.
