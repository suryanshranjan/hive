# Gate 76 predictions: flight tests of hive start as shipped after Gates 66–75

Registered Nov 1 2026, before the flights. The user is away for a day: "whatever is necessary".

## Why this test

Since the last flight (Gate 54), Hive shipped five changes:
- builders ask first;
- overnight questions for the morning;
- a 90-s ask;
- one answer for a repeated question;
- the business-builder split.

Each was tested in the lab harness and has unit tests. None has flown through the real `hive start` end to end. Flights found real faults twice before (Gates 52, 54).

## Setup

- **The job:** Gate 54's: Tiny Shop, a three-part goal (refunds, loyalty points, a daily sales summary).
- **The owner and the score:** the private policy and 27 hidden acceptance tests in `private/g54`, scored in Gate 54 and reused here. The synthetic owner (Gate 54's brief) answers every terminal prompt and every keyboard read.
- **Driver:** `referee/flight76.py` (Gate 52's driver), starting from an empty `~/.hive`.
- **Two flights:**
  - **live:** `hive start` with the owner at the keyboard. The law should pick 3 builders, so the split engages.
  - **overnight:** `hive start --overnight`, then `hive morning` at the keyboard.
- Analysis `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| F1 | Live: no crash, one branch delivered | 80% |
| F2 | Live: the split engages (the last builder has the business role, the others "build the rest") and every question to the owner comes from the business builder | 60% |
| F3 | Live: ≥ 24 of 27 hidden after | 75% |
| F4 | Live: ≤ 45 owner prompts | 70% |
| F5 | Overnight: no crash; ≥ 5 questions recorded overnight; the morning fix round runs | 65% |
| F6 | Overnight: ≥ 22 of 27 hidden after the morning | 60% |

## Decision rules

- Any crash or failed mechanism is a product fault: fix it, test it, and fly again.
- Results within the predictions confirm the shipped flow.

## Limits

- One flight per mode, on one small project, with a synthetic owner. The hidden tests were written in Gate 54 and are reused.
- About $10.
