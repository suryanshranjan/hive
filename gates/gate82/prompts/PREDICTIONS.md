# Gate 82 predictions: Gate 81's flights again, after its two claim fixes

Registered Nov 1 2026, before the flights.

## Why this test

Gate 81 found two faults, now fixed and unit-tested, but not flown:
1. **One builder claimed every derived area.** Now a claim may hold at most an even share, ⌈areas ÷ builders⌉.
2. **A builder whose claim was refused built and landed anyway.** Now `hive land` refuses, with exit 9, a lock name this builder does not hold.

A third change also flies here: derived areas are re-derived for each build's own goal.

## Setup

- Gate 81's flights, unchanged: Tiny Shop, its three-part goal, the private policy and 27 hidden tests (`private/g54`), and the synthetic owner.
- **live:** `hive start`; **overnight:** `hive start --overnight`, then `hive morning`. `~/.hive` starts empty for each.
- Driver `referee/flight82.py`, analysis `referee/analyze.py`, both committed now.
- A dry run of the analysis on Gate 81's flights failed Q2 and Q3 and held Q1, Q4 and Q5, as it should.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| Q1 | Live: no crash, one branch, ≥ 24 of 27 | 75% |
| Q2 | Both flights: no part built by 2 or more builders | 70% |
| Q3 | Both flights: every lock holds at most an even share of the areas, and where there are as many areas as builders, ≥ 2 builders landed work | 70% |
| Q4 | Overnight: no crash, ≥ 22 of 27 after the morning, the fix round ran | 65% |
| Q5 | Both flights: all three functions are delivered (no part left unbuilt by a refusal) | 85% |

## Decision rules

- **Q2, Q3 and Q5 hold:** the fixes stand.
- **Q5 fails:** the refusals strand work. Then the even share must adapt when a builder stops early.
- **A crash:** a fault; fix it and fly again.

## Limits

- One flight per mode, with a synthetic owner. The number of builders depends on the interview.
- About $5.
