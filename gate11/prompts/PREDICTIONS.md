# Gate 11 predictions, registered before the rules exist (Oct 27 2026)

**Question.** Gate 8 found one law across two rule-givers: each answered question fixes about half of the edge errors still left on its function (p ≈ 0.55), so returns diminish. If that is right, giving every function a question before any function gets a second beats spending questions in blocks of 3. If Gate 6's original reading is right (the first question is weak, the third strong), blocks win. This gate runs the two head to head, with the headroom imbalance that misled Gate 6 designed out.

**Design (one command: `python3 lab/run_gate.py lab/experiments/g11_spread_vs_blocks.json`).**
- **Rules.** A fresh independent rule-giver (`gate5/prompts/rulegiver_brief.md`) writes 20 rules into `private/g11/`. They are checked mechanically and not edited.
- **Stage 1.** Team **N0** (3 builders, no questions) runs alone and is scored on the hidden suite (seed 11200000).
- **Pairing.** The 20 functions are sorted by N0's edge errors and paired with their neighbour (10 pairs). A coin seeded `random.Random(11000)` picks the "hi" function of each pair.
- **Stage 2.** Two teams of 3 builders, same rules, same prompt and ask text, 30 questions each, enforced per function by the server:
  - **S (spread):** 2 questions on each hi function, 1 on each lo function.
  - **B (blocks):** 3 on each hi function, 0 on each lo function.
- **Measure.** Errors fixed = a function's edge calls right minus N0's. **R = errors fixed by S / errors fixed by B**, summed over all 20 functions, with a 95% interval bootstrapped over pairs.

**What the hypotheses predict for R** (pre-flight Monte Carlo, `gate11/referee/power.py`; per-function noise from Gates 6 and 8, 20,000 runs):

| Hypothesis | Median R | P(R ≥ 1.15) | P(R ≤ 1.0) |
| --- | --- | --- | --- |
| Diminishing returns, p = 0.55 (Gate 8 law) | 1.41 | 0.90 | 0.02 |
| Diminishing returns, p = 0.40 | 1.28 | 0.70 | 0.12 |
| Linear returns (allocation does not matter) | 1.00 | 0.22 | 0.51 |
| Convex, Gate 6's raw reading (0.25 / 0.55 / 0.92) | 0.88 | 0.09 | 0.72 |

| # | Prediction |
| --- | --- |
| P1 | Spread beats blocks: R ≥ 1.15 |
| P2 | Blocks work where they are spent: B's 3-question functions fix ≥ 0.75 of their N0 edge errors (law 0.91; Gates 6, 8: 0.92, 0.87) |
| P3 | The first question is not weak: S's 1-question functions fix between 0.35 and 0.75 of their errors (law 0.55) |
| P4 | Third estimate of p, fitted on S and B together by least squares on errors fixed (as `gate8/referee/share_fixed.py`): between 0.40 and 0.70 |
| P5 | Treatment delivered: at least 27 of 30 allowed questions used in each of S and B |
| P6 | Rules not guessable: N0 below 70% hidden |

Kills and decision rules:
- **R ≤ 1.0:** the diminishing-returns law is wrong for allocation. Withdraw "one question per function first" and restore blocks as the default.
- **1.0 < R < 1.15:** inconclusive. Change no design rule until a repeat on a new rule-giver.
- **P3 fails low (< 0.35):** Gate 6's weak first question was real, not only an imbalance.

**Honest prior.** About 60% that P1 holds.

**Cost.** About $9 at list price (rule-giver about $0.8, 9 builders about $2.5 to $3 per team); about 15 minutes.

**Note on scoring.** N0's edge errors are used twice: to form pairs and as the baseline for both arms. Both arms share that baseline, so regression to the mean affects S and B alike and cancels in R.
