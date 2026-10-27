# Gate 21 results: a cached guard on a CPU-limited machine, Oct 27 2026

**Question.** Gate 10 saw the same 12-worker project finish in 3.5 minutes on 24 cores, against Gate 3's 8.7 on 2 CPUs, and blamed the guard: every landing runs the full visible suite twice. Is CPU really the bottleneck, under control? And does a guard that reuses main's results help?

**Answer.**
- **Yes, CPU sets the finish, now measured under control.** On the same machine, limited to 4 CPUs for 24 workers, Gate 3's setup took **12.1 minutes** (unlimited, Gate 10: 3.5). G1 held.
- **Caching main's results helped, less than predicted.** The cached guard finished in **10.2 minutes**, 0.84× the baseline (registered target 0.75×; kill threshold 0.95×). 61% of main-result lookups hit the cache. G2 failed, G3 held.
- **Safety held.** One commit on main broke one passing test under the cached guard (fixed by the end); none under the old guard. Gate 10's runs had 1 and 3 such commits.
- **A model of the finish (from this run):** finish ≈ 5.9 minutes of other work + 3.1 minutes per full-suite run per landing on this load. The old guard costs 2 runs per landing; the cache brought it to 1.39.

## Setup

- **Project.** Gate 3's scale seed: 1,340 visible tests in 127 categories.
- **Teams, run at the same time,** 12 workers each, same prompt (Gate 3's `prompt_scale.md`):
  - **F12:** Gate 3's guard (`gate3/tools/land.py`).
  - **C12:** the cached guard (`tools/land.py`). Same checks; main's suite results are stored per commit on the machine, and after a successful push the lander stores its own run as the new main's result.
- **CPU limit.** `docker update --cpus 4` for the swarm phase: 24 workers on 4 CPUs (Gate 3: about 20 on 2). The attempt to lift it with `--cpus 0` did not take effect, so replays also ran on 4 CPUs. That made scoring slower only; replays do not use worker timing.
- Predictions were pushed before the run (commit c757c39).

| Team | Guard | Builder cost | Worker minutes | Finish | Reached 1,290 | Tail | Commits that broke a passing test | Hidden at finish |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F12 | Gate 3's | $14.31 | 12.3–24.2 | **12.1 min** | 10.6 | 1.6 | 0 | 2,211/2,220 |
| C12 | cached | $15.17 | 10.3–13.1 | **10.2 min** | 9.7 | 0.6 | 1 (1 test, fixed) | 2,215/2,220 |

Total $29.47 at list price. All 24 workers exited cleanly. One F12 worker ran 24.2 minutes, well after main was finished; finish times are read from main, not from workers.

C12's guard cache: **154 hits, 100 misses** (61% hits). A miss happens when two workers land close together and the newest main commit has not yet been stored.

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| G1 | finish(F12) ≥ 6.0 min under the CPU limit | **Held**: 12.1 (3.5 unlimited, Gate 10) |
| G2 | finish(C12) ≤ 0.75 × finish(F12) | **Failed**: 10.2 / 12.1 = **0.84** |
| G3 | ≥ 60% of C12's lookups hit the cache | **Held**: 61% (154 of 254) |
| G4 | C12's breaking commits ≤ F12's + 2, none broken at the end | **Held**: 1 against 0; fixed by the end |
| G5 | Both finish all 1,340 visible tests | **Held** |
| Kill | finish(C12) ≥ 0.95 × finish(F12) | **Did not fire** |

Hidden failures at finish are in the same categories as Gate 10's (`concat`, `json_modify`, `strftime`): the referee's SQLite version, not gaming (see `gate10/RESULTS.md`).

## What it means

### 1. The serial gate, measured

| Setup | Cores per worker | Finish |
| --- | --- | --- |
| Gate 10 F12, unlimited | about 1 per worker (24 cores, 24 workers) | 3.5 min |
| Gate 21 F12, 4 CPUs | 1 per 6 workers | 12.1 min |
| Gate 21 C12, 4 CPUs, cached guard | 1 per 6 workers | 10.2 min |
| Gate 3 F12, 2 CPUs (cloud, other load) | 1 per 10 workers | 8.7 min |

Limit 2 of the law says a serial gate caps landings at (1−f)/t_g. Here t_g, the time to run the guard's check, grows with CPU contention, and the swarm's finish grows with it: 3.5× from 24 to 4 CPUs. Gate 3's 8.7 minutes on 2 CPUs is out of line with this (a different machine and load), so the comparison across gates stays a hint.

### 2. A two-term model (model, from one run)

With r full-suite runs per landing:

```
finish ≈ a + b · r       a = 5.9 min (building and workers' own test runs),  b = 3.1 min per run per landing (this load)
```

Fitted on two points (r = 2 gives 12.1; r = 1.39, the measured miss rate plus one, gives 10.2), so it is exactly determined, not tested. It predicts that a guard with r = 1 (every lookup a hit) would finish in about 9.0 minutes, and that the remaining 5.9 is the floor for guard improvements on this load.

### 3. Why the cache missed 39% of the time

A lander reads main's results right after rebasing. If another worker pushed seconds earlier and is still storing its run, the result is not there yet, so the lander runs it again. Waiting a few seconds for a pending store, or having the pusher store before pushing, would raise the hit rate.

## Design consequences

- **Adopt the cached guard.** Same safety in this run, 16% faster on a CPU-bound machine, and no cost on a large one.
- **Give swarms cores.** At about 1 core per 6 workers, the guard dominates; at 1 per worker it barely matters.
- **Next guard improvement:** store before pushing, then check only the categories the change touches plus a sample of the rest. The model's floor (about 5.9 minutes here) bounds what any guard change can buy.

## Honest odds

- A guard with near-100% cache hits finishes ≤ 0.8× the old guard on this load: about 60%.

## Limits

- One run per team. The model's two parameters are fitted on exactly two points.
- `--cpus 0` did not remove the limit; noted above.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md`, `tools/land.py`, `run.sh` | Predictions, the cached guard and the run script, pushed before the run |
| `referee/regressions.py` | Commits on main that broke a passing test (validated on Gates 3 and 10) |
| `results/` | Replays, results, guard cache stats, cost per worker, run log |
| `swarms/*.bundle`, `logs/` | Both teams' histories; the 5 worker logs that exist |
