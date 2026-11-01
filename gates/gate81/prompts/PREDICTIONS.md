# Gate 81 predictions: Gate 76's flights again, after derived areas became the default

Registered Nov 1 2026, before the flights. The user: "Go on".

## Why this test

- **Gate 80 made derived areas the default:** when a project has none, Hive names the goal's parts with a model and builders must claim those names.
- **`hive start` never configures areas** (it writes `areas: {}`), so every real owner's build now runs with derived areas.
- **That meets Gate 74's split.** The last builder owns every part that turns on the owner's decisions; the others are told to build everything else and not to touch those parts.
  - On a goal like Tiny Shop's (refunds, loyalty points, a sales summary), every derived part may be a business part. The other builders would then have nothing they may claim, or would claim a part and build what the business builder owns.
  - The lab tests of Gate 80 had no owner and no split, so this was never flown.
- Flights found faults twice before (Gates 52, 54).

## Setup

- Gate 76's flights, unchanged: Tiny Shop, its three-part goal, the private policy and 27 hidden tests (`private/g54`), and the synthetic owner (Gate 54's brief).
- **live:** `hive start` with the owner at the keyboard.
- **overnight:** `hive start --overnight`, then `hive morning`.
- `~/.hive` starts empty for each flight.
- Driver `referee/flight81.py` (Gate 76's), analysis `referee/analyze.py`, both committed now.
- The analysis was dry-run on Gate 76's flights: R1, R3, R4 and R5 held there, and R2 failed (no areas then).

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| R1 | Live: no crash, one branch, ≥ 24 of 27 hidden | 75% |
| R2 | Live: areas were derived (≥ 2) and the split engaged | 80% |
| R3 | Live: no part (refund, points earned, sales summary) built by 2 or more builders | 60% |
| R4 | Live: ≤ 45 owner prompts | 75% |
| R5 | Overnight: no crash, ≥ 22 of 27 after the morning, the fix round ran | 60% |

## Decision rules

- **A crash, R1 or R5 failing, or builders unable to claim anything:** a product fault. Fix it, test it, and fly again.
- **R3 failing:** the split and derived areas conflict. Then the business builder's parts should be its areas, and the others should claim only the rest.

## Limits

- One flight per mode, on one small project, with a synthetic owner.
- About $5.
