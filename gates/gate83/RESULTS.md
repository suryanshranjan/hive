# Gate 83 results: the flights again, after Gate 82's fix, Nov 1 2026

**Question.** With landed areas protected, do the derived-area claims fly cleanly?

**Answer.**
- **The claim protocol now flies cleanly in both flights:**
  - 3 builders, one area each, every builder landed once;
  - nothing built twice;
  - no claim beyond an even share, and no landing without a lock.

  Q2, Q3, Q4 and Q5 held.
- **But the live build scored 14 of 27 (Q1 failed), for a reason outside claiming.**
  - The owner told the business builder (w3) that a mixed card and store-credit payment is refunded both ways ("700 to the card and 300 as store credit"). w3 then added `card` and `store_credit` keys to `refund()`'s result.
  - The goal had fixed the result as exactly `{'amount': …, 'method': …}`, so 13 hidden refund tests fail on the extra keys.
  - w3 had asked 3 questions, which meets Gate 68's rule for skipping the hand-over ("They asked you 3 questions while building, and your answers are built in"). No code sheet or spot check ran to catch it.
- **Overnight scored 25 of 27 after the morning,** the same as Gates 81 and 82.

| Flight | Builders | Locks | Parts built twice | Questions | Hidden | Owner prompts |
| --- | --- | --- | --- | --- | --- | --- |
| Live | 3, split on | 3, one area each | 0 | 3 (w3) | **14 of 27** (13 fail on the result's extra keys) | 22 |
| Overnight | 3 | 3, one area each | 0 | 16 recorded | 17 → 25 of 27 after the morning | 16 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| Q1 | Live: no crash, one branch, ≥ 24 of 27 | **Failed:** 14 (result shape changed after an owner answer; review skipped) |
| Q2 | Both flights: no part built by 2+ builders | **Held:** 0 and 0 |
| Q3 | Claims within an even share; ≥ 2 builders landed | **Held** |
| Q4 | Overnight: no crash, ≥ 22 after the morning, fix ran | **Held:** 25 |
| Q5 | All three functions delivered | **Held** |

## What it means

1. **The claim protocol for derived areas is done.** Gates 80–83 together:
   - areas named from the goal;
   - an even share per claim;
   - no landing without a lock;
   - landed areas not reclaimed.

   Across the last three flights, nothing was built twice and every builder had work.
2. **A new gap: skipping the hand-over trusts every answer to be built in correctly.** Gate 68's rule (skip after 3 or more questions) was measured with a referee that scored behaviour, not the shape of the result. One spot check of a refund would have shown the extra keys.
   - Candidate, not yet tested: when the long review is skipped, still check the delivered code against the interfaces the goal states (names, arguments, the result's exact form), at no cost to the owner.
   - It needs its own gate.

## Limits

- One flight per mode, with a synthetic owner whose answers vary between flights (the live interview gave 10 rules here; Gate 82's gave 18).

## Files

`prompts/`, `referee/` (`flight83.py`, `analyze.py`).

`results/live/`, `results/overnight/`:
- the terminal, prompts and replies;
- scores;
- each builder's report;
- the run log.
