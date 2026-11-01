# Gate 84 results: check the goal's stated interfaces when the review is skipped, Nov 1 2026

**Question.** Gate 83 lost 13 of 27 hidden tests because a builder added keys to a result the goal had fixed, and the skipped review missed it. Does a check against the goal's stated interfaces catch and repair that, without crying wolf?

**Answer.**
- **Yes. All four predictions held.**
  - **On Gate 83's build:** the check found the extra keys, one builder put `refund()`'s result back to exactly `{amount, method}`, and the build went from **14 to 26 of 27**. The repair took about a minute and $0.17 of builder time, and no owner time.
  - **The builder kept the owner's answer without breaking the form.** It moved the card and store-credit split into a new `refund_breakdown()`, and said so in its land message: "Mixed-payment split can't appear in refund() form, so it's only available via refund_breakdown."
- **In two new live flights it did not cry wolf:**
  - **live1:** the builders asked fewer than 3 questions, so the full review ran (61 prompts) and the check was not needed; 27 of 27.
  - **live2:** the review was skipped after 5 questions. The check ran, found nothing, and the build delivered 26 of 27.
  - The referee's own re-check found no interface problem in either delivery.

| Case | Review | Check | Found | Repair | Hidden |
| --- | --- | --- | --- | --- | --- |
| Gate 83's live build | skipped (3 questions) | ran | `refund()`: extra `card`, `store_credit` | 1 builder, about a minute | 14 → **26 of 27** |
| Flight live1 | full (61 prompts) | not needed | – | – | 27 of 27 |
| Flight live2 | skipped (5 questions) | ran | nothing | – | 26 of 27 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| I1 | Gate 83's build: found, fixed, 0 left, ≥ 24 of 27 | **Held:** 26 |
| I3 | Both flights: no crash, one branch, ≥ 24 | **Held:** 27, 26 |
| I4 | Both flights: 0 interface problems delivered | **Held** |
| I5 | Both flights: the check ran where the review was skipped; fix if needed | **Held** |

## Disclosed

- The check was written while looking at Gate 83's failure and tried on 8 earlier delivered builds (it flagged only Gate 83's live build). That was development, so it is not scored.
- The referee's re-check (I4) uses the same code as the product, with its own model call reading the goal, so it is not an independent judge of the interfaces. The hidden tests are.

## What changes in Hive

- **The interface check stays on** (`hive/contract.py`; `hive/start.py` `_keep_contract`, run where the review is skipped).
  - It checks only what a goal states outright: a function's file, its name, its arguments, and the exact keys of a dict result written as a literal.
  - Anything else is left alone. `HIVE_CONTRACT_CHECK=0` turns it off.
- **Tests:** `tests/test_assistant.py` (extra keys and a missing function found; matching code left alone), and `tests/fake_explain.py` (the goal's interfaces in the start flows).

## Limits

- One repaired build and two flights, on one small project, with a synthetic owner.
- A result built up in steps, or a list or object result, is not checked.

## Files

`prompts/`, `referee/` (`fix84.py`, `flight84.py`, `analyze.py`).

`results/fix/` (before and after scores, the problems found).

`results/live1/`, `results/live2/`:
- the terminal, prompts and replies;
- scores;
- the run log.
