# Gate 22 results: store-before-push guard, a held-out test of Gate 21's finish model, Oct 27 2026

The first attempt died at the account's usage limit and was not scored (`ABORTED.md`). This is the rerun from scratch, with the same predictions (commit 4f5dc4e) and a fresh login.

**Question.** Gate 21 fitted finish ≈ 5.9 + 3.1 · r minutes (r = full-suite runs per landing) on two points. Storing results before pushing was meant to push the cache hit rate near 100% and r near 1. Does the finish land where the model says?

**Answer.**
- **The cached guard helped again, by more than in Gate 21:** 10.9 minutes against 15.1 for Gate 3's guard (**0.72×**; Gate 21: 0.84×). No commit on main broke a passing test in either team.
- **But storing before pushing did not raise the hit rate** (58%, against 61% in Gate 21), so r stayed near 1.4. At that hit rate the model predicted 0.85×; the observed 0.72× misses it by 0.13. H1 failed, though the kill threshold (0.15) did not fire.
- **The misses have a clear cause:** half the commits on main (38 of 76) were lock or withdraw commits from `claim.py`. They change no code, but the cache is keyed by commit, so each one starts uncached. **Keying the cache by the code's content** (the tree hash of `minisql/` and `run_tests.py`) would make those hits. That is the next fix.
- **The baseline varies a lot between runs:** Gate 3's guard took 12.1 minutes in Gate 21 and 15.1 here, on the same setup. So the two-term model's absolute numbers are not reliable. The ratio within a run is the quantity to trust: 0.84 and 0.72 at about 60% hits, mean **0.78**.

## Setup

As registered: Gate 3's scale seed and prompt, two teams of 12 run together on a container limited to 4 CPUs (lifted to 24 for scoring). **F12** uses Gate 3's guard; **S12** uses Gate 21's cached guard with one change, storing its own results under its commit before pushing (`tools/land.py`). All 24 workers exited without API errors.

| Team | Guard | Builder cost | Finish | Reached 1,290 | Tail | Commits that broke a passing test | Cache hits | Hidden at finish |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F12 | Gate 3's | $16.57 | **15.1 min** | 13.5 | 1.6 | 0 | n/a | 2,215/2,220 |
| S12 | store before push | $15.68 | **10.9 min** | 10.6 | 0.3 | 0 | 175 of 301 (58%) | 2,212/2,220 |

Total builder cost $32.25 for the rerun ($19.15 more for the aborted attempt). One S12 worker ran 28.8 minutes, long after main was finished.

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| H1 | finish ratio within ±0.08 of the model at the measured hit rate (h = 0.58, r = 1.42: model 0.85) | **Failed**: observed **0.72** (off by 0.13) |
| H2 | hit rate ≥ 0.90 | **Failed**: 0.58 |
| H3 | S12's breaking commits ≤ F12's + 2, none broken at the end | **Held**: 0 and 0 |
| H4 | finish(F12) between 9.5 and 14.5 minutes | **Failed**: 15.1 |
| H5 | Both finish all 1,340 visible tests | **Held** |
| Kill | ratio misses the model by more than 0.15 | **Did not fire** (0.13) |

Hidden failures at finish are in the same version-sensitive categories as Gates 10 and 21 (referee SQLite version; see `gate10/RESULTS.md`).

## What it means

### 1. Why storing before pushing did not help

| Commits on main during the run | Count | Cached by the end |
| --- | --- | --- |
| Landings (through `land.py`) | 38 | 35 |
| Locks and withdrawals (through `claim.py`) | 38 | 24 |

A lander looks up main's results right after rebasing. Half the time main's tip is a lock commit that nobody has run, because claims bypass the guard. The first lookup at each such commit misses, and workers rebasing at about the same moment all miss together. Lock commits never touch `minisql/` or `run_tests.py`, so a cache keyed by that content would serve them from the landing below. **Design change:** key the guard cache by the tree hash of the tested code, not by commit.

### 2. The finish model, revised

| Run | r | F12 finish | Cached finish | Ratio |
| --- | --- | --- | --- | --- |
| Gate 21 | 1.39 | 12.1 | 10.2 | 0.84 |
| Gate 22 | 1.42 | 15.1 | 10.9 | 0.72 |

The baseline moved by 3 minutes between two runs of the same setup, so a two-point fit of absolute times was over-precise. What replicates is the direction and rough size: caching main's results saves about a fifth of the finish (0.78×, range 0.72 to 0.84) on a CPU-bound machine at about 60% hits. The two-term model is kept only as a rough guide (model, held out once, and missed by 0.13).

## Design consequences

- **Keep the cached guard** (two runs, 0.84× and 0.72×, no extra breakage).
- **Key the cache by code content** (tree hash of `minisql/` plus `run_tests.py`), so lock commits hit. Predicted hit rate ≥ 0.85.
- **Treat single scale runs as ±25% on absolute time;** compare only teams run together.

## Honest odds

- A content-keyed cache reaches ≥ 85% hits: about 75%. It cuts the finish further (ratio ≤ 0.7): about 50%, given the noise.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md`, `tools/land.py`, `run.sh` | Predictions, the guard and the run script, pushed before either attempt |
| `ABORTED.md`, `aborted_run/` | The first attempt (usage limit), not scored |
| `results/` | Replays, results, cache stats, cost per worker, run log |
| `swarms/*.bundle`, `logs/` | Both teams' histories; the worker logs that exist |
