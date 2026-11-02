# Gate 101 results: silent drift, Nov 2 2026

**Question.** When the owner's rules have changed and he does not say so, does Hive's memory make the old rules stick?

**Answer.**
- **No, the reverse. Memory helped against silent drift.**
  - With his day-1 rulings kept (M), the day-2 builds scored 27, 28 and 29 of 29 on his new policy.
  - Without them (F), they scored 20, 29 and 17.
  - All three predictions failed, two of them in the good direction.
- **Why memory helped: it is what notices the change.**
  - In M, his day-2 answers pulled against his day-1 rulings 3–5 times per flight, and Hive asked "which holds now?". The changed rules became explicit, and the builders changed the code.
  - In F there was no earlier ruling to compare with, so the change surfaced later or not at all. **Correction, after reading the transcripts:** the new rate was not unknown in F; it never reached the code the product runs.
    - **F1 (20):** the code sheet showed the old rate, and the owner corrected seven points rules to a point per ₹50. One change builder got all seventeen corrections in its prompt and changed only the refund rules. Hive then said "Your changes are in, and every test passes."
    - **F3 (17):** the owner stated the new rate in the interview. The builder wrote it in a new `shop/points.py` that nothing calls, left `shop/loyalty.points_earned` at a point per ₹100, and missed the 7-day refund window. The review was skipped.
    - The builders' own tests passed both times. Nothing checked the owner's words against the functions the product uses (MAST FM-3.2/3.3). This is now Gate 103.
- **What this shows:** for a change to an existing product, Hive notices a changed rule only if it remembers the old one. Without memory, nothing compares the owner's answers with what the existing code already does.

| Day 2 (new policy, not announced) | Hidden (of 29) | Prompts | Contradictions settled |
| --- | --- | --- | --- |
| M: memory kept | 27, 28, 29 | 43, 50, 49 | 3, 5, 3 |
| F: no memory | 20, 29, 17 | 61, 33, 31 | 0 |

- **Day 1:** 26 of 27 on the old policy, 34 prompts.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| D1 | F's median ≥ 26 of 29 | **Failed:** 20 |
| D2 | M's median ≤ F's − 5 (memory makes drift stick) | **Failed:** 28 vs 20 (memory helps) |
| D3 | M asks fewer prompts than F | **Failed:** 49 vs 33 |

## What it means

1. **Keep the memory.** Gates 92 and 101 together: whether the owner announces the change or not, his kept rulings plus the contradiction check carry his latest word into the code. They cost him a few "which holds now?" questions.
2. **Check the owner's examples against the product's own functions before delivery** (Gate 103). Both F failures were verification failures, not missing knowledge.

## Files

`prompts/`, `referee/` (`flight101.py`, `analyze.py`).

`results/day1/`, `results/day2_M1` to `results/day2_F3`:
- the terminal, prompts and replies;
- scores;
- the run log.
