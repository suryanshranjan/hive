# Gate 85 results: the baseline, five live flights of the shipped flow, Nov 2 2026

**Question.** How reliable is `hive start` as shipped, how much does it ask of the owner, and where does Hive's own money go? This is the baseline for the gap plan (`docs/gap_plan.md`).

**Answer.**
- **Reliable 4 times in 5, not 5 in 5.**
  - pass^1 = 0.80; pass^5 failed. One flight scored 20 of 27 even after the full review.
  - Median hidden score: 27 of 27.
- **It asks too much.** The median flight put **55 prompts** to the owner (33 to 67), and he typed 690 to 2,405 words.
  - The interview alone is about 14 to 19 prompts.
  - Most of the rest are the review's spot checks: 12 to 32 "Right?" cases per flight.
- **Hive's own model spend is 4.8 to 8.6× the builders'** ($2.64 to $5.48 against $0.52 to $0.88).
  - **45% goes to interpreting the interview's answers:** `interview.settled_by`, `_amend` and `_rule`.
  - **19% to reading the owner's free-text replies** (`telegram.understand`, used in the terminal too).
  - **22% to the spot checks** (`apply_one`, `recheck`, `find`).
  - The builders' cost is the small part.

| Flight | Hidden | Prompts | Words typed | Minutes | Builders | Hive's own |
| --- | --- | --- | --- | --- | --- | --- |
| live1 | 27 | 59 | 1,347 | 12.2 | $0.88 | $4.21 (4.8×) |
| live2 | 27 | 55 | 1,151 | 11.4 | $0.56 | $3.32 (5.9×) |
| live3 | 27 | 67 | 2,405 | 15.3 | $0.64 | $5.48 (8.6×) |
| live4 | **20** | 53 | 690 | 9.5 | $0.55 | $2.84 (5.2×) |
| live5 | 24 | 33 | 834 | 7.4 | $0.52 | $2.64 (5.1×) |

- **Why live4 failed:**
  - The owner's rule was "an order already refunded gets nothing the second time". The builder recorded refunded orders in a module-level set that lives as long as the program, keyed by order id.
  - Any later refund of an order with the same id then returns 0. 7 hidden refund tests fail this way.
  - The review ran in full: 15 rules, then 32 spot checks. It did not catch the bug, because each spot check looks at one case at a time and never sees state carried between calls.
  - **MAST labels:**
    - FM-3.2, no or incomplete verification;
    - FM-1.1, disobey task specification (`refund()` was specified to take the order, the days and the reason, not to remember the past).
- **Only live5 skipped the review** (its builders asked 3 or more questions). Its interface check found nothing, and it scored 24.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| B1 | pass^1 ≥ 0.8 | **Held:** 0.80 (at the line) |
| B2 | pass^5 | **Failed:** live4 scored 20 |
| B3 | Median prompts > 30 | **Held:** 55 |
| B4 | Hive's own ≥ 4× builders' in every flight | **Held:** 4.8 to 8.6× |

## Disclosed

- The spot checks' model cost was never counted with Hive's own before this gate (`spotcheck.find`). It is now, so earlier gates' "Hive's own" figures were slightly low.

## What it means (the targets for the next gates)

1. **Gap 3, Hive's own spend:**
   - Interpreting the interview's answers (45%) and the owner's free text (19%) costs more than all the building.
   - These are short reading tasks, run on the CLI's default model. The first test is a small, cheap model for them, scored on the same 27 hidden tests; Gates 62–65 tested only builders' models.
2. **Gap 2, owner load:** the spot checks are most of the prompts (12 to 32 per flight). They found real errors before (Gate 63: +7.6 points), but none in live4's failure.
   - The first test: show the 5 highest-stakes cases, not 20 to 30, and compare hidden and prompts with this baseline.
3. **Reliability:** the one failure was hidden state across calls, which neither the review nor the interface check looks for.
   - A cheap check, and a candidate: ask builders to keep business functions free of state that outlives a call unless the goal asks for it, and have the guard flag module-level mutable state.

## Files

`prompts/`, `referee/` (`flight85.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
