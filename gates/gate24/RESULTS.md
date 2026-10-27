# Gate 24 results: Hive v1 end to end, Oct 27 2026

**Question.** Gates 3 to 23 tested Hive's parts one at a time, mostly with 3 workers. Does the whole v1 design work as one system, with twice the team size?

**Answer: yes. Every registered prediction held.**
- **Hive v1 got intent right:** 95.0% of hidden tests, against 53.0% for the same swarm without the intent interface (+42.0 points, CI +32.4 to +51.8).
- **The swarm stayed safe at 6 workers:** no commit on main broke a passing visible test, in either team.
- **The parts worked together:** all 17 questions used, all 27 tour tests passing, and the content-keyed guard served 15 of 17 lookups from its cache.

## Hive v1, as run here

- **Coordination:** silent workers, category claims through git locks, guarded landings, tests as the referee (Gates 1 to 3).
- **Guard:** the content-keyed cached guard (`gates/gate23/tools/land.py`), installed in both teams' starting repos with the new `"guard"` option of `run_gate.py`.
- **Intent:** the owner's decision tour (one worked example per policy decision, 50 in all, as 27 visible tests) plus 17 builder questions, with answers as tests.

## Setup

- **Rules.** A fresh independent rule-giver with Gate 13's brief (1 to 4 declared decisions per function, five functions each; one example per decision, disjoint from the hidden inputs). Checked mechanically and not edited. Predictions were pushed before the rules existed (commit 437aaf2).
- **Teams, 6 workers each,** same prompt, seeds and guard: **N0** (no tour, no questions) and **V1** (tour and 17 questions).
- **Hidden suite.** 500 tests (seed 24200000), 70% edge calls. Not committed. Per-commit replays (`--replay`) give the breakage check.

| Team | Builder cost | Visible | Hidden tests | 95% CI by function | Commits that broke a passing test | Questions |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | $3.43 | 1,380/1,380 | **265/500 (53.0%)** | 43.4–63.2% | 0 | 0 |
| V1 | $3.45 | 1,407/1,407 | **475/500 (95.0%)** | 89.6–100.0% | 0 | 17 of 17 |

Rule-giver $1.18; total $8.06 at list price. All 12 workers exited without API errors. Guard cache: 15 hits, 2 misses (both teams share one machine, each with its own cache key).

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| V1 | V1 ≥ 93% hidden | **Held**: 95.0% |
| V2 | V1 − N0 ≥ +35 points | **Held**: +42.0 (CI +32.4 to +51.8) |
| V3 | No breaking commit still broken at the end in either team; V1 at most 2 breaking commits | **Held**: 0 and 0 |
| V4 | V1 uses ≥ 15 of 17 questions and passes every tour test; both pass every visible test | **Held**: 17; 27/27; 1,380 and 1,407 |
| V5 | N0 below 70% | **Held**: 53.0% |
| Kill | V1 < 85% | **Did not fire** |

## What it means

The pieces measured separately combine without loss at 6 workers:

| Owner has | Interface | Hidden pass | Gates |
| --- | --- | --- | --- |
| A decision list | tour + 17 questions, 3 workers | 95.2%, 98.2% | 13, 17 |
| A decision list | tour + 17 questions, 6 workers, cached guard | **95.0%** | **24** |

This is the integration test for building the product: the v1 design (silent swarm + cached guard + owner's decision tour + questions) is the measured baseline.

## Limits

- One run per team, one rule set, agent owner.
- Speed was not measured here: on 24 cores and with a small visible suite, intent gates finish in a few minutes either way (`gates/gate10/referee/makespan.py` is built for the scale project's 1,340-test suite and does not apply).

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions, pushed before the rules existed |
| `referee/oracle.py` | Rules, decisions and tour, unsealed after scoring (synthetic) |
| `results/` | Summary, probes, per-commit replays, every question and answer, guard cache stats, cost per worker, run log, rule-giver output |
| `swarms/*.bundle`, `logs/` | Both teams' histories; worker logs |
