# Gate 88 results: a handful of spot checks, not 12–32 (Gap 2), Nov 2 2026

**Question.** Gate 85's median flight put 55 prompts to the owner, most of them spot checks. With at most 6 spot checks, round-robin across the parts, does the owner's load fall without losing accuracy?

**Answer.**
- **The registered claim fired.** Median prompts fell from 55 to 34 (0.62×). All five flights succeeded (pass^1 1.00, against 0.80), and the median hidden score stayed at 27.
- **Part of the drop is luck, not the cap.** In three of the five flights the builders asked 3 or more questions, so the review was skipped and the cap never applied. In Gate 85 that happened once in five.
- **Comparing only flights where the review ran:**
  - Gate 88 asked 51 and 44 prompts, against 53 to 67 (median 57) in Gate 85: about 0.8×.
  - Both scored 27 of 27; Gate 85's four review flights included the 20 of 27.
  - Two flights are too few to separate the cap's effect from chance.
- **Hive's own spend did not fall** (L4 failed: $3.51 against $3.70). Finding the spot checks still costs the same; only fewer are shown.

| Flight | Review | Prompts | Hidden |
| --- | --- | --- | --- |
| Gate 85 live1–4 | ran | 59, 55, 67, 53 | 27, 27, 27, 20 |
| Gate 85 live5 | skipped | 33 | 24 |
| Gate 88 live2, live3 | ran (at most 6 spot checks) | 51, 44 | 27, 27 |
| Gate 88 live1, live4, live5 | skipped | 34, 34, 31 | 27, 26, 25 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| L1 | Median prompts ≤ 0.7× Gate 85's | **Held:** 34 vs 55 (helped by 3 skipped reviews) |
| L2 | pass^1 ≥ 0.8 | **Held:** 1.00 |
| L3 | Median hidden ≥ 26 | **Held:** 27 |
| L4 | Hive's own spend ≤ 0.85× Gate 85's | **Failed:** 0.95× |
| Claim | L1, L2 and L3 | **Fired** |

## What changes in Hive

- **At most 6 spot checks by default,** as the registered rule says (`HIVE_SPOT_MAX`, default 6).
  - It ships after Gates 89 and 90 finish, so their flights run on unchanged code.
  - With the caveat above, the next baseline will show its effect more clearly.
- **The interview is now the larger part of what is left:** 14 to 17 prompts per flight. That is Gap 2's next target.

## Files

`prompts/`, `referee/` (`flight88.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
