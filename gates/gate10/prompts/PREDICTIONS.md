# Gate 10 predictions, registered before the run (Oct 27 2026)

**Question.** At 12 workers, Gate 3's finish time was set by its tail: 1,290 of 1,340 tests passed at 5.3 minutes, and the last 50 (the JSON family, claimed as one worker's third task) took another 2.9 (`gates/gate10/referee/makespan.py` on Gate 3's replay). Scheduling theory says claiming the largest task first (LPT) bounds the finish within 4/3 of optimal, against up to 2 − 1/N for arbitrary order. **Does largest-first claiming cut the finish time?**

**Correction to the queued card.** The card said to rank categories by failing-test count. Every category has exactly 10 tests, so that ranks nothing. The work that was late in Gate 3 was a *family* of categories sharing machinery (13 `json_*`, 11 `window_*`). So "largest" here means **the family with the most failing unheld categories**.

**Design (`sh gates/gate10/run.sh` in the lab container).**
- **Project.** Gate 3's scale seed (`gates/gate3/seed_scale.bundle`): 1,340 visible tests in 127 categories, 28 passing at the start.
- **Teams, run at the same time on the same machine** (24-core laptop, Docker), 12 workers each:
  - **F12:** Gate 3's scale prompt, unchanged.
  - **L12:** the same prompt with one change in step 1 (`gates/gate10/prompts/prompt_largest.md`): take 1 to 3 categories from the family with the most failing unheld categories; only when no family has 3 or more left, choose freely.
- **Measures** (`gates/gate10/referee/makespan.py`, `gates/gate10/referee/events.py`, validated on Gate 3's replay and logs, which they reproduce: tail 2.9 min, conflicts per landing 0.44):
  - finish: from the first worker start to the first commit on main where all 1,340 visible tests pass;
  - tail: finish minus the first commit reaching 1,290;
  - conflicts per landing;
  - hidden pass at finish, on Gate 2's regenerated hidden suite (seed 5000000, 20 per category; never committed).
- Timings are not comparable with Gate 3's (2-CPU cloud box); only F12 against L12 counts.

| # | Prediction |
| --- | --- |
| P1 | Largest-first finishes sooner: finish(L12) ≤ 0.85 × finish(F12) |
| P2 | The tail shrinks: tail(L12) ≤ 0.5 × tail(F12) |
| P3 | No gaming: both reach every hidden test at their finishing commit (2,260/2,260) |
| P4 | Clustering costs little: conflicts per landing in L12 ≤ F12 + 0.15 |
| P5 | Both swarms finish all 1,340 visible tests |

Kill: **finish(L12) ≥ finish(F12)**. Claim order is not what sets the finish at 12 workers on this machine, and the tail needs another fix (for example splitting families, or self-registering modules).

**Honest prior.** P1 about 55%; P2 about 55%; P4 about 60%. One run per team: a single slow worker can swing a finish by minutes.

**Cost.** About $20 to $25 at list price (24 workers); about 15 to 20 minutes including replays.
