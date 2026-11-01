# Gate 80 results: areas named from the goal's parts, when none are configured, Nov 1 2026

**Question.** In Gate 78, with no areas configured, builders claimed the same functions under different names and rebuilt them twice. If Hive turns the goal's parts (which it already asks a model for, to size the team) into the areas builders must claim, does the duplicated work stop, and does it save money?

**Answer.**
- **Duplicated work stopped: 5.7 of 12 functions to 0, in every run.** It saved 10% of the cost, not the 15% registered, so the claim did not fire. The registered fallback rule applies: duplicated work stopped (D1), with no loss in accuracy (D3) or time (D4), at the price of one model call. **It ships, on by default.**

| Means over 3 runs | Functions rebuilt by 2+ builders (of 12) | Builders' cost | Hidden (of 61) | Wall, preparing included |
| --- | --- | --- | --- | --- |
| F: free-text claims (as shipped) | **5.7** (12, 0, 5) | $1.37 | 55.7 | 3.1 min |
| A: areas from the goal's parts | **0.0** (0, 0, 0) | $1.24 | 55.3 | 2.9 min |

- **Free-text claims fail in two ways:**
  - **One builder claims everything.** In F1, w1 took the lock `all12` and rebuilt all 12 functions while three others did the same work under their own names. All 12 were rebuilt twice, and F1 cost $1.68, the most of any run.
  - **Two builders cut the job differently.** In F3, one lock named the generator helpers and another named functions by name; 5 functions were built twice.
- **F2 duplicated nothing:** its builders happened to cut the job into three non-overlapping lists. It cost $1.17, the same as the A runs. Free-text claims can work; they cannot be relied on.
- **Named areas held:** with 10 areas, each a file and its functions, `hive claim` refused any other name, and no function was built twice in 3 runs. Gate 79 (one area per bug report) also had none.
- **Naming the parts took 6 seconds** (one model call). Its names differ between calls: A3's were shorter than A1's and A2's.
- **Across Gates 78 and 80,** the 7 runs without areas rebuilt 7, 6, 1, 6, 12, 0 and 5 functions twice.

## Setup

- **The job:** Gate 78's: sqlglot 30.27.0 with 12 functions emptied and named in the goal; the seed has no areas; 61 hidden test methods.
- **Arms**, each 4 builders through the product, with no owner and 30 minutes:
  - **F:** as shipped;
  - **A:** `hive.swarm.prepare(derive_areas=True)`. `hive.law.part_names` names the goal's parts, and they are committed to the shared branch as areas, each shown to builders with the part's words.
- **Duplicated work** is measured from each builder's own commits, landed or not (its clone's reflog; `referee/dup.py`): a builder rebuilt a function if one of its commits turned it from emptied into code.
- **Order:** F1, A1, A2, F2, F3, A3, each alone.
- Predictions pushed before any run (`992e1da`). Builders cost $7.81 in all.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| D1 | A's duplicated ≤ half of F's, and F's ≥ 2 | **Held:** 0.0 vs 5.7 |
| D2 | A's cost ≤ 0.85× F's | **Failed:** 0.90× |
| D3 | A's hidden ≥ F's − 3 | **Held:** 55.3 vs 55.7 |
| D4 | A's wall ≤ 1.1× F's | **Held:** 0.94× |
| Claim | D1, D2 and D3 | **Did not fire**; the registered fallback (D1, D3 and D4 held) ships it |

## What changes in Hive

- **Derived areas ship, on by default** (`hive/swarm.py` `prepare`, `hive/law.py` `part_names`, `area_names`).
  - When a project has no areas configured and there are 2 or more builders, Hive names the goal's parts with one model call. It commits them to the shared branch as the areas to claim, and shows each builder the part each area stands for.
  - Configured areas are never touched. `HIVE_DERIVE_AREAS=0` turns it off.
- Tests in `tests/test_run.sh`: derived areas reach the shared branch and the prompt; configured areas are kept.

## Limits

- Three runs per arm, on one job whose parts are named outright in the goal. A goal in plain words may split less cleanly, and a part the model names twice, or misses, is not tested.
- Duplicated work cost less than expected, because a duplicate builder often stops when its landing conflicts.

## Files

`prompts/PREDICTIONS.md`.

`referee/`: `run80.py` (driver), `dup.py` (duplicated work), `analyze.py`.

`results/<run>/`:
- the result (areas, locks, who rebuilt what, scores, cost);
- the run log;
- the agents' accounts.

`results/analysis.txt`.
