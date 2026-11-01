# Gate 83 predictions: the same flights again, after Gate 82's fix

Registered Nov 1 2026, before the flights.

## Why this test

Gate 82's claim fixes held (even shares; no landing without a lock), but live, two builders reclaimed each other's landed areas: a landed area showed as "free". Now, within a build:
- `hive areas` shows "landed by …";
- `hive claim` refuses a landed area unless the builder passes `--again`, to fix something it found wrong.

Unit-tested; not flown.

## Setup

Gate 82's flights and analysis, unchanged (`referee/flight83.py`, `referee/analyze.py`): Tiny Shop's three-part goal, the private policy and 27 hidden tests, and the synthetic owner. One live flight, then one overnight flight followed by the morning.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| Q1 | Live: no crash, one branch, ≥ 24 of 27 | 75% |
| Q2 | Both flights: no part built by 2 or more builders | 70% |
| Q3 | Both flights: claims within an even share; where areas allow, ≥ 2 builders landed | 75% |
| Q4 | Overnight: no crash, ≥ 22 of 27 after the morning, the fix round ran | 65% |
| Q5 | Both flights: all three functions delivered | 90% |

## Decision rules

- **All hold:** the claim protocol for derived areas is done.
- **Q2 fails again:** read how the part came to be built twice, and fix that path.

## Limits

One flight per mode, with a synthetic owner. About $5.
