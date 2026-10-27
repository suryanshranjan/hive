# Gate 24 predictions, registered before the rules exist (Oct 27 2026)

**Question.** Gates 3 to 23 tested Hive's parts one at a time, mostly with 3 workers. **Does the whole v1 design work as one system, at a larger team size?** This is the integration test before building the product.

**Hive v1, as measured so far:**
- **Coordination:** silent workers; category claims through git locks; guarded landings; tests as the referee (Gates 1–3).
- **Guard:** the content-keyed cached guard (`gate23/tools/land.py`). Its finish-time effect was not scored (Gate 23 aborted), but before the stop its cache served 337 of 338 lookups, and the commit-keyed versions were 0.84× and 0.72× faster with the same safety (Gates 21, 22).
- **Intent:** the owner's decision tour (one worked example per policy decision, as visible tests) plus 17 builder questions, with answers as tests (Gates 13, 17: 95.2%, 98.2%).

**Design (`python3 lab/run_gate.py lab/experiments/g24_v1.json --replay`).**
- **Rules.** A fresh independent rule-giver with Gate 13's brief: 20 functions with 1 to 4 declared decisions each, five functions per count, one example per decision (50) disjoint from the hidden inputs.
- **Teams, 6 workers each** (twice the earlier intent gates), both with the content-keyed guard, the same prompt and seeds:
  - **N0:** no tour, no questions.
  - **V1:** the decision tour and 17 questions.
- **Hidden suite.** 25 tests per function (seed 24200000), 70% edge calls.
- **Measures:** hidden pass; commits on main that broke a passing visible test, from per-commit replays (`gate21/referee/regressions.py`); questions used; guard cache hit rate.

| # | Prediction |
| --- | --- |
| V1 | Hive v1 gets intent right: V1 ≥ 93% hidden |
| V2 | And it is the intent interface doing it: V1 − N0 ≥ +35 points |
| V3 | The swarm stays safe at 6 workers: in each team, no commit on main that broke a passing visible test is still broken at the end, and V1 has at most 2 such commits |
| V4 | Treatment delivered: V1 uses ≥ 15 of 17 questions and passes every tour test; both teams pass every visible test |
| V5 | Rules not guessable: N0 below 70% hidden |

Kill: **V1 < 85% hidden.** The parts that each worked do not combine at 6 workers. Find which part degrades before building the product.

**Honest prior.** V1 about 70%; V2 about 75%; V3 about 85%.

**Cost.** About $12 at list price (12 builders and a rule-giver); about 10 minutes plus replays. Run on its own, spaced from other gates, to stay within the account's usage limit.
