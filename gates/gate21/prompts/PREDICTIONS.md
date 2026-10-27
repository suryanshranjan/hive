# Gate 21 predictions, registered before the run (Oct 27 2026)

**Question.** Gate 10 found the same 12-worker project finishing in 3.5 minutes on 24 cores, against Gate 3's 8.7 on 2 CPUs. The suspected cause is the guard (`tools/land.py`): every landing runs the full 1,340-test visible suite twice, once on a snapshot of main and once on the worker's change, and on a small machine those runs queue for the processor. That was a comparison across machines. This gate tests it under control, and tests a fix.

**The fix: a cached guard** (`gates/gate21/tools/land.py`). The check is unchanged: no test that passes on current main may fail with the change. But main's suite results are now stored per commit on the machine. After a successful push, the lander stores its own run as the result for the new main commit, so the next lander usually finds main's results already computed and runs the suite once instead of twice. Duplicate-definition checks and regression checks are otherwise identical.

**Design (`gates/gate21/run.sh`).**
- **Project.** Gate 3's scale seed (1,340 visible tests, 127 categories).
- **Teams, run at the same time,** 12 workers each, same prompt (Gate 3's `prompt_scale.md`):
  - **F12:** Gate 3's guard.
  - **C12:** the cached guard; nothing else differs.
- **CPU limit.** The container is limited to 4 CPUs for the swarm phase (`docker update --cpus 4`): 24 workers on 4 CPUs, near Gate 3's density of 20 workers on 2. The limit is lifted for scoring.
- **Measures:** finish and tail (`gates/gate10/referee/makespan.py`), commits on main that broke a passing visible test (`gates/gate21/referee/regressions.py`; Gate 10 baseline: 1 and 3, all fixed by the end), cache hits and misses (C12), and hidden pass at finish (Gate 2's suite regenerated on SQLite 3.49: 2,220 tests).

| # | Prediction |
| --- | --- |
| G1 | The CPU limit reproduces the slowdown: finish(F12) ≥ 6.0 minutes (Gate 10, unlimited: 3.5) |
| G2 | The cached guard is faster: finish(C12) ≤ 0.75 × finish(F12) |
| G3 | The cache works: at least 60% of C12's main-result lookups are hits |
| G4 | No more breakage reaches main: C12's commits that broke a passing test ≤ F12's + 2, and none is still broken at the end |
| G5 | Both swarms finish all 1,340 visible tests |

Kill: **finish(C12) ≥ 0.95 × finish(F12)** while G1 holds. The guard's second suite run is not what slows a CPU-bound swarm.

If G1 fails (F12 under 6 minutes even on 4 CPUs), CPU was not Gate 3's bottleneck either, and Gate 10's 2.5× has another cause (for example the cloud box's disk or network); G2 is then still scored but read as a small-effect test.

**Honest prior.** G1 about 65%; G2 about 50%; G3 about 75%; G4 about 80%.

**Cost.** About $25 to $30 at list price (24 workers; Gate 10 cost $29.09); 20 to 30 minutes including replays.
