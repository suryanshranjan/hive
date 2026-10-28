# Gate 43 results: a talking swarm against a silent one, Oct 29 2026

**Question** (from the user). If the builders can talk to each other for high-level coordination, does the swarm get faster or better?

**Answer.**
- **No difference, either way.** With a shared message board, two teams of 6 finished the scale project in 3.6 and 3.5 minutes. Two silent teams took 3.5 and 3.4. Cost was $4.18 and $4.22 against $4.21 and $4.10. All four teams passed 1,340 of 1,340 visible tests and 99.7–99.8% of the hidden suite.
- **They used the board, a little, and sensibly.** Each talking team posted 4–5 messages, all of them useful:
  - "landed X; now building all window functions in `minisql/window.py`";
  - "the tail of `functions.py` is a conflict hotspot, keep both import lines when rebasing";
  - "aggregate calls may now carry FILTER/ORDER BY: use `e[:4]`, not a 4-way unpack".
  - These are exactly what claim files and commit messages already carry in a silent team, so the extra channel changed nothing measurable.
- **Why, in the model's terms:** this swarm's finish is set by onboarding and the guard's CPU, not by missing coordination. Collisions were already rare and cheap. Talking can only win back the collision cost, a few percent, and on this project there was almost none to win.
- **Hive stays silent.** By its letter the registered kill for talking fired ("not faster, and costlier"), but the cost difference was 1%, inside the noise. The honest reading is no effect. A harder, more tightly coupled project, or more workers, could still show one. Ideas from the board worth keeping are below.

## Setup

- **Project.** The Gate 2/3 scale project: a SQL engine from 362 to 1,340 visible tests in 127 categories. Hidden suite from `gen2.py` (seed 5000000, 20 per category), generated privately, never committed. Left out: `median`, `percentile` and `transactions`, where this machine's SQLite (3.53.1) disagrees with the stored visible answers (Gate 10's rule). That leaves 2,200 scored hidden tests.
- **Teams.** 6 workers each, protocol v2 (claims and the guard), each team alone on the 2-CPU machine, in ABBA order: S1, T1, T2, S2. Predictions, driver and analysis were pushed before any team ran (`0d9d45e`).
  - **S (silent):** Gate 3's scale prompt, unchanged.
  - **T (talking):** the same prompt plus `tools/board.py` (post to everyone, read new messages). Workers were asked to read it at every sync and use it for high-level coordination.

| Team | Finish (last landing) | Wall | Cost | Landings | Visible | Hidden | Messages (posters) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 3.5 min | 5.5 min | $4.21 | 20 | 1,340/1,340 | 99.7% | – |
| T1 | 3.6 min | 5.6 min | $4.18 | 17 | 1,340/1,340 | 99.8% | 5 (4) |
| T2 | 3.5 min | 5.2 min | $4.22 | 19 | 1,340/1,340 | 99.8% | 4 (4) |
| S2 | 3.4 min | 5.5 min | $4.10 | 17 | 1,340/1,340 | 99.8% | – |

Means: finish S 3.5 vs T 3.6 minutes (ratio 1.03); cost S $4.15 vs T $4.20 (1.01).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| T1 | Finish ratio between 0.85 and 1.15 | **Held:** 1.03 |
| T2 | Talking costs ≥ 10% more | **Failed:** 1.01. Reading the board cost almost nothing |
| T3 | Hidden within 2 points | **Held:** +0.1 |
| T4 | Each talking team posts ≥ 6 messages | **Failed:** 5 and 4 |
| T5 | Conflicts plus guard blocks per landing, T ≤ S | **Held, but uninformative:** most workers did not export their event log (as in Gate 10), so only 5 landings were logged |
| Ship | T ≥ 20% faster in both pairings | **Did not fire** |
| Kill | T not faster and costlier | **Fired by its letter** (1.03× time, 1.01× cost); read as no effect |

## What it means

1. **Coordination was not the bottleneck.** Six workers took the whole project in 3.5 minutes either way. Gate 3 needed 8.7 minutes with 8 workers and an earlier model. The swarm's limits stay where the law puts them: onboarding, the guard's CPU, and the longest task.
2. **What talking looks like when allowed:** announcements of shared machinery, hotspots and interface changes. Hive's silent design already carries the first in claim files. The other two, warnings about a merge hotspot and a changed internal interface, are the kind of thing that could matter on a bigger, more coupled codebase. That case is untested: this project had almost no collisions to prevent.
3. **A cheap middle path, if it is ever needed:** have the land step ask for one line of "what others should know", and show the last few at each sync. That is talking through git, with no new channel. Not built: no evidence yet that it pays.

## Limits

- One project, 6 workers, finishes of 3.5 minutes. With so little time in each run, differences under about 15% could not be seen.
- 2 CPUs: earlier repeats varied by ±25% (Gate 21), though these four teams agreed within 6%.
- Workers were told to use the board but did so lightly. A design that forces talking (for example, a plan agreed before claiming) was not tested.

## Files

`prompts/` (both prompts, predictions), `tools/board.py`, `referee/` (driver, analysis), `results/` (analysis, both boards, worker costs, per-team pass counts and commit histories, run log), `swarms/` (all four teams' histories), `logs/`.
