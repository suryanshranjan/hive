# Gate 102 predictions: the interview before an overnight build

Registered Nov 2 2026, before the flights.

## Why this test

- **Gate 99:** overnight flights succeed only 3 in 5. The failures miss decisions no night builder thought to record (half refunds, final-sale double points, the 500-rupee minimum).
- **Overnight has no interview**, though the owner is at the keyboard when he types `hive start --overnight`. The live path, which has it, succeeds 5 of 5 (Gates 95, 96, 98).
- **Splitting the night builders did not help** (Gate 77, +0.7 of 27).

## The change (branch `dev102`, merged after Gates 100 and 101 finish)

- `hive start --overnight` runs the same interview first ("Before you go, a few quick situations, so they start from your rules").
- The builders then work the night without asking. The morning questions cover what is left.

## Setup

- **Gate 99's five overnight flights,** after the merge. Driver `referee/flight102.py`, analysis `referee/analyze.py` (Gate 99's, with N2 and N3 adjusted as below), committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| N1 | pass^1 ≥ 0.8 | 65% |
| N2 | Median after the morning ≥ 26 | 60% |
| N3 | Median prompts (interview and morning) ≤ 35 | 65% |
| N4 | Mean cost ≤ $1.50 | 80% |

## Decision rules

- **N1 and N2 hold:** the interview before an overnight build ships.
- **N1 fails:** read which decisions were still missed.

## Limits

Five flights; one project; a synthetic owner. About $8.
