# Gate 3 results, Oct 27 2026

Gate 3 had three steps. Step 1 built protocol v2. Step 2 ran it at larger swarm sizes. Step 3, the intent test, is built but has not run yet; see `README.md` in this folder. Predictions were registered before launch in `prompts/PREDICTIONS.md`.

## Step 2: scale with category claims and guarded landing

**Setup.** The Gate 2 project (1,340 visible tests in 127 categories, 362 passing at the start) with protocol v2:

- `tools/claim.py` claims named test categories. It refuses any overlap and withdraws the later claim when two collide.
- `tools/land.py` refuses a landing that adds a duplicate definition, or that fails any test which passes on main.

Two swarms launched at the same time on one 2-CPU machine, as in Gate 2. The 24-worker swarm got only 8 workers: this session caps concurrent agents at 20, so its workers 9 to 24 never started. It is reported here as **F8**; its files keep the original `F24-wN` names.

| Swarm | Workers | Tokens | Per worker | Minutes to all 1,340 | Landings | Conflicts per landing | Landings blocked by guard | Hidden (2,260 + 700) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F8 | 8 | 1.23M | 154k | 10.4 | 36 | 0.36 | 1 (would have broken 10 tests) | 2,260/2,260 and 700/700 |
| F12 | 12 | 1.61M | 134k | 8.7 | 36 | 0.44 | 1 (would have broken 20 tests) | 2,260/2,260 and 700/700 |
| Gate 2, 6 workers | 6 | 963k | 161k | 8.2 | | 0.33 | no guard | 2,260/2,260 |
| Gate 2, 12 workers | 12 | 1.62M | 135k | 7.8 | | 0.48 | no guard; 1 regression reached main | 2,260/2,260 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| S1 | Tokens = 111k per worker + 3.0k per category: 12 workers ≈ 1.63M | **Held.** 1.61M (1% off). The same law gives 1.19M for 8 workers; observed 1.23M (4% off). This is the third project size it has predicted. |
| S2 | Finer claims lower the floor: 12 workers under Gate 2's 7.8 min | **Failed.** 8.7 min. |
| S3 | 24 workers buy little over 12 | **Not tested**: only 8 of 24 started. Partial: 12 workers were 1.20× faster than 8 for 1.5× the workers. |
| S4 | The guard keeps regressions off main | **Held at every push.** Both would-be regressions were blocked and fixed. But see the bisect note below. |
| S5 | No category held by two locks | **Held** by construction. Duplicated machinery still happened: workers rebuilt small parsers that sat under another worker's lock. |
| S6 | No gaming: visible and hidden within 1 point | **Held.** At most 0.40 points apart at any commit, on matching categories, in both swarms. |

**Bisect note.** Replaying every commit finds 2 broken commits in each history: one would have broken 20 visible and 40 hidden tests, the other 10 visible and 20 hidden. Each is the commit the guard blocked. It was immediately followed by the same worker's fix, and `land.py --continue` pushed both together, so the tip of main was never broken. The history, though, is not bisect-clean. Fix: `--continue` should fold the fix into the blocked commit before pushing.

## Why S2 failed: the tail

Twelve workers reached 1,290 of 1,340 at 5.8 minutes. The last 50 tests took another 2.9 minutes, done by one worker while the other eleven had stopped. Those 50 tests were the JSON extensions, which F12-w10 had claimed as its third task. F8 shows the same pattern: 1,320 at 8.8 minutes, then one worker finished RETURNING and INTEGER PRIMARY KEY alone at 10.4.

Finish time is set by the last big task that starts late, not by the number of workers:

- **Established (scheduling theory):** makespan ≥ max(total work / N, longest task). Greedy claiming in arbitrary order can be up to (2 − 1/N) × optimal. Claiming the largest task first (LPT) is within 4/3 of optimal.
- **Protocol change for the next run:** a worker claims the largest unclaimed failing category first. The guard's cost also matters: it runs the full suite twice per landing on a shared 2-CPU machine.

## Where conflicts come from

Nearly every rebase conflict (16 in F12, 13 in F8) was two workers adding a line at the same registration point: the function table in `engine.py` or the imports in `parser.py`. Each took about a minute. Category claims did not reduce them, because the shared registration lines, not the categories, are what collide. Letting each module register itself would remove most of them. That is a shaper's job (lower κ).

## Files

- `swarms/F12.bundle`, `swarms/F8.bundle`: full histories (`git clone swarms/F12.bundle`).
- `logs/`: CLAIM, LAND, CONFLICT and BLOCKED events for every worker.
- `results/tokens.csv`: tokens, tool calls and duration per worker.
- `results/eval_F12.json.gz`, `results/eval_F8.json.gz`: every first-parent commit replayed against the visible suite, the 2,260 Gate 2 hidden tests and the 700 Gate 1 hidden tests, with per-test results.
