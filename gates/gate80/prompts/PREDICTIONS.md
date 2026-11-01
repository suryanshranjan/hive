# Gate 80 predictions: areas named from the goal's parts, when none are configured

Registered Nov 1 2026, before any run.

## Why this test

- **Gate 78 observed:** with no areas in `.hive/config.json`, any claim name is accepted. Builders claimed the same functions under different names and rebuilt them twice.
  - Measured after the fact from the builders' own commits, landed or not (`referee/dup.py`): 7, 6, 1 and 6 of the 12 emptied functions were rebuilt by 2 or more builders in Gate 78's four runs.
- **Gate 79**, with one area per bug report, had no duplicated work. That was observed, not tested.
- **`hive start` writes an empty `areas`** unless the owner configured some, so every owner who has not is in Gate 78's position.
- **Hive already asks a model for the goal's independent parts** (`hive/law.py`, Gate 52) to size the team. It only counts them.
- **This gate:** let those parts become the areas builders must claim (`hive.swarm.prepare(derive_areas=True)`). Does that stop duplicated work, and save cost?

## Setup

- **The job:** Gate 78's: sqlglot 30.27.0 with 12 functions emptied and named in the goal; 61 hidden test methods; `runs/g78_seed` has no areas.
- **Arms**, each 4 builders through the product, with no owner and 30 minutes:
  - **F:** as shipped (free-text claims);
  - **A:** areas from the goal's parts, named by one model call before launch, then committed to the shared branch's `.hive/config.json`. Builders see each area with its part's words, and `hive claim` refuses any other name.
- **Order:** F1, A1, A2, F2, F3, A3, each alone.
- Driver `referee/run80.py`, `referee/dup.py`, analysis `referee/analyze.py`, committed now.

## Measures (means over 3 runs per arm)

- **Duplicated:** of the 12 functions, how many 2 or more builders rebuilt in their own commits.
- **Builders' cost.**
- **Hidden:** passed of 61.
- **Wall minutes,** preparing included.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| D1 | A's duplicated ≤ half of F's, and F's ≥ 2 | 70% |
| D2 | A's cost ≤ 0.85× F's | 45% |
| D3 | A's hidden ≥ F's − 3 | 80% |
| D4 | A's wall ≤ 1.1× F's | 65% |

## Decision rules

- **Claim (D1, D2 and D3):** `hive start` and `hive run` name areas from the goal's parts whenever none are configured, by default.
- **If D1 holds but D2 fails:** duplicated work is not where the money goes. Ship it anyway if D3 and D4 hold, since it costs one model call. Otherwise, no change.
- **If D1 fails:** named areas do not stop builders duplicating. Look at how they claimed.

## Limits

- Three runs per arm, on one job whose 12 parts are named outright in the goal. Goals in plain words may split less cleanly.
- About $10 and about an hour.
