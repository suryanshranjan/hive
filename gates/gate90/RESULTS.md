# Gate 90 results: the business builder fills the placeholders, Nov 2 2026

**Question.** Gate 87 found builds delivered with `PLACEHOLDER (w3 / owner decision)` left in them: the split's "rest" builders landed business parts with placeholders, and the business builder never came back to them. With the business builder allowed to claim any area (landed too, beyond an even share), and told to fill every placeholder, does that stop?

**Answer.**
- **Yes. The claim fired.** No delivery had a placeholder left (0 of 5, against 3 of 10 across Gates 85 and 87). pass^1 0.80, median hidden 27.
- **The one failure is a different fault, Gate 83's again, by another path.**
  - In live5 the owner, asked about a mixed card and store-credit order, insisted in the review: "Show both parts." The change round then added a `split` key to `refund()`'s result and a `'split'` method.
  - The goal fixes the result as exactly `{amount, method}`, so all 12 hidden refund tests fail (15 of 27).
  - Gate 84's interface check would have caught it, but it runs only where the review is *skipped*. Here the review ran.
- **MAST:** FM-1.1 (disobey task specification); the verification is incomplete because it does not cover every path (FM-3.2).

| Flight | Hidden | Prompts | Placeholders left | Review |
| --- | --- | --- | --- | --- |
| live1 | 27 | 33 | none | skipped |
| live2 | 27 | 28 | none | skipped |
| live3 | 27 | 68 | none | ran |
| live4 | 27 | 64 | none | ran |
| live5 | **15** | 74 | none | ran; result shape changed by a correction |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| J1 | No placeholder left in any delivery | **Held** |
| J2 | pass^1 ≥ 0.8 | **Held:** 0.80 |
| J3 | Median hidden ≥ 26 | **Held:** 27 |
| J4 | Median prompts ≤ 1.2× Gate 85's | **Held:** 64 vs 55 (1.16×) |
| Claim | J1, J2 and J3 | **Fired** |

## Disclosed

- **The machine's disk filled at 05:59, as live5 finished.** live5's code is intact, and its failure is the result-shape change above, not the disk.
- The gates queued after it (89, 91 and 92) failed at once and are being rerun. Scored run copies from Gates 78–80 and 86 were deleted to make room; their results were already in `gates/`.

## What changes in Hive

1. **The fix stays on main** (merged before these flights).
2. **Next: the interface check runs before every delivery,** not only when the review is skipped. live5 shows that a review's corrections can break a stated interface just as builders' answers can (Gate 83). It ships with the next registered gate, after Gates 89 and 91, which run on the code they were registered with.

## Files

`prompts/`, `referee/` (`flight90.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
