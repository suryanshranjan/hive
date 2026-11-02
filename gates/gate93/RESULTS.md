# Gate 93 results: confirmation of Hive as now shipped, Nov 2 2026

**Question.** Flown together, are the fixes and changes since Gate 85 at least as good as the baseline, and lighter for the owner? They are:
- the business builder fills placeholders;
- at most 6 spot checks;
- the interface check before every delivery;
- technical goals skip the interview and the review.

**Answer.**
- **Lighter, as reliable, and still not 5 in 5.**
  - **The owner's load fell by 40%:** a median of 33 prompts, against 55 in Gate 85 and 64 in Gate 90 (C3 held).
  - **pass^1 stayed at 0.80** (C1 held). No delivery broke an interface the goal states (C4 held).
  - **pass^5 failed again** (C2): live1 scored 19 of 27.
- **Why live1 failed:** a reasonable owner rule, built with an unsafe default.
  - The owner answered that "only delivered orders can be refunded". A builder added `delivered: bool = False` to `Order`, so every existing order, the hidden tests' included, counts as undelivered and gets 0. 8 refund tests fail.
  - The 6 spot checks led with unusual cases (a cancelled order marked damaged), so none showed the most ordinary refund. Nothing else catches a new field whose default changes what existing callers get.
  - **MAST:** FM-1.1 (the goal's `refund(order, days, reason)` now depends on a field the goal never mentions), FM-3.2 (incomplete verification).
- **The failures that break pass^5 are a family, one per flight:**
  - state kept between calls (Gate 85);
  - a result's form changed (Gates 83, 90);
  - a new field whose default changes behaviour (here).

  Each passes the builders' own tests and the owner's review. Each would show in the most ordinary case.

| Flight | Hidden | Prompts | Words typed | Review | Hive's own |
| --- | --- | --- | --- | --- | --- |
| live1 | **19** | 51 | 1,800 | ran (6 checks) | $4.65 |
| live2 | 25 | 43 | 1,550 | ran | $3.77 |
| live3 | 27 | 32 | 1,351 | ran | $2.95 |
| live4 | 27 | 33 | 913 | ran | $2.82 |
| live5 | 27 | 27 | 1,094 | ran | $2.38 |
| *Gate 85 baseline* | *27, 27, 27, 20, 24* | *median 55* | | | *mean $3.70* |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| C1 | pass^1 ≥ 0.8 | **Held:** 0.80 |
| C2 | pass^5 | **Failed:** live1 19/27 |
| C3 | Median prompts ≤ 45 | **Held:** 33 |
| C4 | No delivery breaks a stated interface | **Held** |

## What it means

1. **The new baseline:** 33 prompts, pass^1 0.80, median hidden 27, Hive's own spend 5–9× the builders'.
   - Interpreting the owner's words (`understand`, `_amend`, `settled_by`, `_rule`) is now 74% of Hive's own spend.
2. **The next reliability lever:** show the most ordinary case of each part first. Today the spot-check finder looks for "choices the owner might not expect", so a plain refund of a plain order is never shown. This is a one-line change to its brief, to be registered and tested against this gate.

## Files

`prompts/`, `referee/` (`flight93.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
