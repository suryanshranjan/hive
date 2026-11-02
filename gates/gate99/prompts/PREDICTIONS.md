# Gate 99 predictions: the overnight path, after everything since Gate 83

Registered Nov 2 2026, before the flights. The user: "Go on test more open items".

## Why this test

Every change since Gate 83 was flown live only:
- the placeholder fix;
- at most 6 spot checks;
- the interface check before every delivery;
- the ordinary case first;
- the lean reader;
- the helper-following check.

The overnight path (`hive start --overnight`, then `hive morning`) has its own flow: questions recorded at night, answered in the morning, then a fix round. Flights found faults twice when changes met (Gates 81, 87).

## Setup

- **Five overnight flights** on main as pushed (`ce32296`): Tiny Shop, the private policy and 27 hidden tests, and the synthetic owner answering the morning questions.
- Driver `referee/flight99.py` (Gate 98's, overnight mode), analysis `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| N1 | pass^1 ≥ 0.8 (≥ 24 of 27 after the morning) | 55% |
| N2 | Median hidden after the morning ≥ 25 | 60% |
| N3 | Median morning prompts ≤ 20 | 70% |
| N4 | Mean cost per flight ≤ $1.50 | 75% |

## Limits

Five flights; one project; a synthetic owner. About $8.
