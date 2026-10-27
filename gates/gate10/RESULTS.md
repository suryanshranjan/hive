# Gate 10 results: largest-first claiming at 12 workers, Oct 27 2026

**Question.** Gate 3's 12-worker swarm finished at 8.7 minutes, held up by a 2.9-minute tail: one late-claimed family of categories (JSON) done by one worker at the end. Scheduling theory says claiming the largest task first should cut that. Does it?

**Answer.**
- **No. Largest-first was slower,** 4.3 minutes against 3.5, with a longer tail (0.7 against 0.1). The kill condition fired: claim order is not what sets the finish time here.
- **Why: the baseline already started the big work early.** Without being told to, Gate 3's prompt had workers claim `json_*` at 0.3 minutes and `window_*` at 0.4. With 12 workers and only a handful of big families, the first round of claims covers them anyway. Gate 3's late JSON claim was one run's bad luck, not the protocol's.
- **The bigger finding is the machine.** Both swarms finished in 3.5 to 4.3 minutes, against Gate 3's 8.7 on a 2-CPU cloud box, with the same seed and protocol. Every guarded landing runs the full suite twice, so on 2 CPUs twelve workers queued for the processor. That is limit 2 of the law (a serial gate caps landings at (1−f)/t_g) showing up as CPU time per gate check. More cores shrank t_g.
- P1, P2 and P3 failed; P4 could not be tested; P5 held.

## Setup

- **Project.** Gate 3's scale seed: 1,340 visible tests in 127 categories, 28 passing at the start. Every category has exactly 10 tests, so the queued card's "rank by failing-test count" would have ranked nothing; "largest" was defined by family (categories sharing a prefix) and registered as such.
- **Teams, run at the same time** on a 24-core laptop in Docker, 12 workers each:
  - **F12:** Gate 3's scale prompt, unchanged.
  - **L12:** the same prompt, with step 1 changed to "take 1 to 3 categories from the family with the most failing unheld categories" (`prompts/prompt_largest.md`).
- Predictions were pushed before the run (commit f1f7a15).

| Team | Builder cost | Worker minutes | Claims | Withdrawn | Landing commits | Finish | Reached 1,290 | Tail | Hidden at finish |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F12 | $13.52 | 4.2–7.5 | 32 | 0 | 35 | **3.5 min** | 3.3 min | **0.1 min** | 2,211/2,220 |
| L12 | $15.57 | 5.5–7.9 | 32 | 0 | 35 | **4.3 min** | 3.6 min | **0.7 min** | 2,210/2,220 |

Total $29.09 at list price, above the registered estimate of $20 to $25. Finish times come from replaying every commit on main (`gates/gate2/referee/evaluate.py`, then `referee/makespan.py`), counted from the first worker's start.

**Treatment delivered.** L12's first five claims were the `window`, `json`, `date`, `insert` and `cte` families, in that order (0.2 to 0.4 minutes). F12's first twelve claims also included `json` (0.3 min) and `window` (0.4 min).

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| P1 | finish(L12) ≤ 0.85 × finish(F12) | **Failed**: 4.3 against 3.5 (1.23×) |
| P2 | tail(L12) ≤ 0.5 × tail(F12) | **Failed**: 0.7 against 0.1 |
| P3 | Both pass every hidden test at their finishing commit | **Failed as registered**: 2,211 and 2,210 of 2,220. Both teams fail the same categories (`concat` 5, `json_modify` 3 and 4, `strftime` 1), which points to the referee version (below), not to gaming |
| P4 | Conflicts per landing in L12 ≤ F12 + 0.15 | **Not testable**: only 4 of 24 workers wrote their event log (`HIVE_LOG`), so conflicts were not recorded. Git shows 32 claims and 0 withdrawals for each team |
| P5 | Both swarms finish all 1,340 visible tests | **Held** |
| Kill | finish(L12) ≥ finish(F12) | **Fired**: claim order does not set the finish at 12 workers here |

## Two measurement problems, found and disclosed

1. **The referee's SQLite version.** `gen2.py` uses the installed SQLite to compute expected answers. Checked against the 1,340 stored visible answers, the container's SQLite 3.40.1 disagreed on 95 and the host's 3.49.1 on 21 (all of `median` and `percentile`, plus one `concat`). The hidden suite was therefore generated on the host and has 2,220 tests (no `median` or `percentile`) instead of 2,260. The remaining shared hidden failures sit in categories where SQLite versions differ, which is why P3 is read as a referee artefact. Gate 2's exact SQLite version is not recorded; it should be in the README next to the seeds.
2. **`gen2.py` did not run on Python 3.11** (backslashes inside f-string expressions). Four lines were rewritten with the strings moved to module constants. The regenerated suite is byte-for-byte identical (2,220 files compared).

## What it means

- **Limit 3 (tail):** Gate 3's tail was real but not systematic. With families this size and 12 workers, ordinary claiming starts the big work in the first half-minute. Largest-first added nothing, and here it was slower (one run; a single slow worker can swing a finish by a minute).
- **Limit 2 (the gate):** on more cores the same swarm finished 2.5× faster. On a shared small machine, the guard's double full-suite run per landing is the bottleneck. Model, not measured directly: finish ≈ max(work / N, landings × t_g / cores).
- **Design consequence:** keep Gate 3's claiming. To go faster, cut the guard's cost (run only affected categories, or one suite run per landing) and give swarms enough cores. Largest-first is dropped.

## Honest odds

- The guard's CPU cost, not claim order, sets the finish on a 2-CPU machine: about 70% (one cross-machine comparison, not a controlled one).

## Limits

- One run per team. The comparison with Gate 3 crosses machines, so the 2.5× is not a controlled measurement.
- Event logging failed for most workers; the prompt asks them to `export HIVE_LOG`, and most did not.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md`, `prompts/prompt_largest.md`, `run.sh` | Predictions, the changed prompt and the run script, pushed before the run |
| `referee/makespan.py`, `referee/events.py` | Finish time and tail from the replay; event counts from worker logs (both validated on Gate 3) |
| `results/eval_*.json.gz`, `results/results.txt`, `results/tokens.csv`, `results/run.log` | Per-commit replays, the summary, cost per worker, run log |
| `swarms/*.bundle`, `logs/` | Both teams' histories; the 4 worker logs that exist |
