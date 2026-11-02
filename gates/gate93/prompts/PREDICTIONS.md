# Gate 93 predictions: confirmation of Hive as now shipped

Registered Nov 2 2026, before the flights.

## Why this test

Since Gate 85's baseline, these changed in the shipped flow, each tested alone:
- the business builder fills its teammates' placeholders (Gate 90);
- at most 6 spot checks (Gate 88);
- the interface check now runs before every delivery (Gate 90's finding: a review correction broke `refund()`'s stated result);
- technical goals skip the interview and the business review (Gates 89, 94; on Tiny Shop's business goal the interview still runs).

Hive's own reading stays on the default model (Gates 87 and 91). Flown together, are they at least as good as Gate 85, and lighter for the owner?

## Setup

- Gate 85's five live flights, on main as merged (`767d66d`), with no setting changed.
- Driver `referee/flight93.py`, analysis `referee/analyze.py`, committed now.
  - The analysis was dry-run on Gate 90's flights: it failed C4 on live5's `split` key, as it should.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| C1 | pass^1 ≥ 0.8 | 70% |
| C2 | pass^5 (all five succeed) | 40% |
| C3 | Median owner prompts ≤ 45 (Gate 85: 55; Gate 90: 64) | 60% |
| C4 | No delivery breaks an interface the goal states | 85% |

## Use

This is the new baseline for what follows.

## Limits

Five flights, one small project, a synthetic owner. About $25.
