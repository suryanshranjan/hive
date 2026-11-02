# Gate 96 results: Gate 95 repeated, Nov 2 2026

**Question.** Gate 95's five flights, with the ordinary case first, all succeeded: pass^5 for the first time. Does it hold on five more?

**Answer.**
- **Yes. All five succeeded again:** pass^1 1.00, pass^5 held, median hidden 27, median 33 prompts.
- **Over Gates 95 and 96, 10 of 10 flights succeeded.** In the five gates before the fix (85, 87, 90, 91, 93), 20 of 25 did, with one failure in almost every set of five.
- **10 runs are still a small sample.** The 95% interval on a 10-of-10 success rate runs from about 69% to 100%. But the one-in-five failure that marked every earlier baseline did not appear in 10 tries.

| Flight | Hidden | Prompts | Minutes | Hive's own |
| --- | --- | --- | --- | --- |
| live1 | 26 | 33 | 10.0 | $2.18 |
| live2 | 26 | 32 | 9.2 | $2.44 |
| live3 | 27 | 25 | 8.3 | $2.43 |
| live4 | 27 | 54 | 15.7 | $4.45 |
| live5 | 27 | 57 | 15.4 | $4.46 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| C1 | pass^1 ≥ 0.8 | **Held:** 1.00 |
| C2 | pass^5 | **Held** |
| C3 | Median prompts ≤ 38 | **Held:** 33 |
| C4 | No delivery breaks a stated interface | **Held** |

## What it means

- **On Tiny Shop with a synthetic owner, Hive as shipped is now reliable:** 10 of 10, against a baseline of 0.80 per flight (Gate 85).
  - The owner's load is about a third lower than Gate 85's (31–33 prompts against 55).
- **Still open:**
  - Hive's own spend: 5–10× the builders'. 75% of it is interpreting the owner's words; the default reader is already Claude Sonnet 5.5, and Haiku lost accuracy.
  - The interview's 12–17 prompts.
  - A harder real codebase.
  - The real founder.

## Files

`prompts/`, `referee/` (`flight96.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
