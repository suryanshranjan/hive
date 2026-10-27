# Gate 23 predictions, registered before the run (Oct 27 2026)

**Question.** Gates 21 and 22 cached main's suite results in the guard and finished in 0.84× and 0.72× the time of Gate 3's guard, but hits stayed near 60%. Gate 22 found why: half the commits on main are lock and withdraw commits from `claim.py`. They change no code, but the cache was keyed by commit, so each started uncached. **Keyed by the code's content, does the cache hit almost always, and does the finish drop further?**

**The change** (`gates/gate23/tools/land.py`, from Gate 22's guard): the cache key is a hash of the tree hashes of `minisql/`, `run_tests.py` and `tests/`, the only things the suite result depends on. Checked before the run on a scratch clone: a lock commit leaves the key unchanged, and a code change changes it. The guard's checks are unchanged.

**Design (`gates/gate23/run.sh`, same as Gates 21 and 22).** Two teams of 12, run together on the container limited to 4 CPUs (lifted to 24 for scoring), Gate 3's scale seed and prompt. **F12:** Gate 3's guard. **K12:** the content-keyed cached guard.

| # | Prediction |
| --- | --- |
| K1 | The content key fixes the misses: K12's hit rate ≥ 0.85 (Gates 21, 22: 0.61, 0.58) |
| K2 | The finish drops further: finish(K12) / finish(F12) ≤ 0.72 (Gate 22's ratio at 58% hits) |
| K3 | Safety: K12's commits that broke a passing test ≤ F12's + 2, and none is still broken at the end |
| K4 | Both swarms finish all 1,340 visible tests |

Kill: **K12's hit rate below 0.70.** The lock commits were not the main source of misses.

**Noise.** The baseline moved from 12.1 to 15.1 minutes between Gates 21 and 22, so K2 compares only teams run together, and a single run can miss it either way.

**Honest prior.** K1 about 75%; K2 about 45%; K3 about 85%.

**Cost.** About $30 at list price; 25 to 35 minutes including replays.
