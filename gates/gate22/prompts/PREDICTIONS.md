# Gate 22 predictions, registered before the run (Oct 27 2026)

**Question.** Gate 21 fitted a two-term model of a CPU-bound swarm's finish: **finish ≈ 5.9 + 3.1 · r minutes**, where r is the number of full visible-suite runs per landing (12 workers per team, 24 workers on 4 CPUs). It was fitted on exactly two points (r = 2: 12.1 min; r = 1.39: 10.2 min), so it has not been tested. Its cached guard missed 39% of lookups because landers stored their results only after pushing. **If landers store before pushing, r should fall to about 1. Does the finish fall to where the model says?**

**The change** (`gates/gate22/tools/land.py`, one edit to Gate 21's guard): the lander stores its own suite results under its commit *before* pushing. Whoever rebases onto that commit finds them. If the push fails, the stored entry belongs to a commit that never reaches main and is never looked up. The checks are unchanged.

**Design (`gates/gate22/run.sh`, same as Gate 21's).**
- **Teams, run at the same time** on the container limited to 4 CPUs, 12 workers each, Gate 3's scale seed and prompt:
  - **F12:** Gate 3's guard (r = 2 by construction).
  - **S12:** the store-before-push guard.
- **Measures:** finish and tail, commits on main that broke a passing test, cache hits and misses, and hidden pass at finish (Gate 2's suite on SQLite 3.49: 2,220 tests).

**What the model predicts.** With S12's measured hit rate h, r = 2 − h, and **finish(S12) / finish(F12) = (5.9 + 3.1 r) / 12.1**. At h = 1, the ratio is 0.74.

| # | Prediction |
| --- | --- |
| H1 | The model holds out: finish(S12) / finish(F12) is within ±0.08 of (5.9 + 3.1·(2 − h)) / 12.1, using S12's measured hit rate h |
| H2 | Storing before pushing fixes the misses: h ≥ 0.90 |
| H3 | Safety: S12's commits that broke a passing test ≤ F12's + 2, and none is still broken at the end |
| H4 | The baseline replicates: finish(F12) between 9.5 and 14.5 minutes (Gate 21: 12.1) |
| H5 | Both swarms finish all 1,340 visible tests |

Kill: **the ratio misses the model by more than 0.15.** The two-term model does not describe the finish, and Gate 21's 16% gain is not explained by suite runs per landing.

**Honest prior.** H1 about 50% (single runs swing by a minute or more); H2 about 80%; H3 about 85%; H4 about 70%.

**Cost.** About $30 at list price; 25 to 35 minutes including replays.
