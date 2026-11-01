# Gate 91 predictions: Hive's own reading on Haiku, on the fixed flow

Registered Nov 2 2026, before the flights.

## Why this test

- **Gate 87:** Haiku 5.5 for Hive's own reading steps cut their spend to 0.11× with pass^1 unchanged, but the median hidden score fell to 25. Two of its flights shipped with placeholders unfilled, a product fault unrelated to the model.
- **Gate 90 fixes that fault.** This gate runs Gate 90's flights again with one change, Haiku for `explain.py`'s calls, and compares with Gate 90.
- The spot-check cap (Gate 88) is not yet the default, so neither gate uses it.

## Setup

- Gate 90's five live flights and code, with `HIVE_EXPLAIN_CMD='claude -p --output-format json --model claude-haiku-5-5'`.
- Driver `referee/flight91.py`, analysis `referee/analyze.py` (Gate 87's, comparing with Gate 90), committed now.
- **Order:** after Gates 90 and 89.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| H1 | Hive's own spend ≤ 0.4× Gate 90's | 80% |
| H2 | pass^1 ≥ 0.8 | 60% |
| H3 | Median hidden ≥ 26 | 60% |
| H4 | Median prompts ≤ 1.2× Gate 90's | 65% |

## Decision rules

- **Claim (H1, H2 and H3):** Haiku becomes the default for Hive's own reading steps.
- **H3 fails again:** find the step that loses quality (Gate 87 saw more re-show loops), and keep the default model for that step.

## Limits

- Five flights against five. About $10.
