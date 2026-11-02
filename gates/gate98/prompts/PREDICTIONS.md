# Gate 98 predictions: the lean reader and the interface check that follows helpers, together

Registered Nov 2 2026, before the flights.

## Why this test

- **Gate 97:** the lean reader cut Hive's own spend to 0.16×, to about the builders' spend.
- **Its one failure was a result built by a helper,** which the interface check could not see. The check now follows same-file helpers. Replayed on 51 delivered builds, it catches all 3 failures of that kind and raises no alarm on a correct build.
- This flies both together, on main as pushed (`80b44ed`).

## Setup

- Gate 97's five live flights, unchanged otherwise. Driver `referee/flight98.py`, analysis `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| F1 | Hive's own spend ≤ 1.5× the builders' (mean per flight) | 80% |
| F2 | pass^5 (all five succeed) | 50% |
| F3 | Median hidden ≥ 26 | 80% |
| F4 | Median owner prompts ≤ 35 | 75% |

## Limits

Five flights, one small project, a synthetic owner. About $6.
