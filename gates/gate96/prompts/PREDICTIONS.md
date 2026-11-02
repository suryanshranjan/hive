# Gate 96 predictions: Gate 95 repeated

Registered Nov 2 2026, before the flights.

## Why this test

- **Gate 95:** with the ordinary case first, all 5 flights succeeded, pass^5 for the first time. That is one flight's difference from Gate 93 (4 of 5).
- **A founder judges by the bad run** (τ-bench's pass^k). One clean set of five is not yet a property of Hive.

## Setup

- Gate 95's five live flights again, on the same code (`6f5475d`), with no setting changed.
- Driver `referee/flight96.py`, analysis `referee/analyze.py` (Gate 95's), committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| C1 | pass^1 ≥ 0.8 | 75% |
| C2 | pass^5 (all five succeed again) | 45% |
| C3 | Median owner prompts ≤ 38 | 70% |
| C4 | No delivery breaks a stated interface | 85% |

## Use

- Over 10 flights (Gates 95–96), pass^1 is estimated from 10 runs.
- Any failure is read and labelled with MAST.

## Limits

Five flights; one small project; a synthetic owner. About $20.
