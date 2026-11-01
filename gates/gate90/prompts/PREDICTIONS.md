# Gate 90 predictions: the business builder fills the placeholders

Registered Nov 2 2026, before the flights.

## Why this test

- **Gate 87 found a product fault**, also present in Gate 85's live5: delivered code still marked `PLACEHOLDER (w3 / owner decision)`.
  - Gate 74's split tells the "rest" builders to leave placeholders for the business builder.
  - Gates 80–82 made every part of the goal an area, gave each builder an even share, and protected landed areas.
  - So a rest builder claims and lands a business part with placeholders. The business builder finishes its own part, finds everything landed, and stops.
- **MAST:** FM-1.2 and FM-2.4 (`docs/failures_mast.md`).

## The change (branch `dev90`, on top of `dev89`; merged to main after Gate 88 finishes)

- **The business builder (named in `run.json`) may claim any area, landed or not, and beyond an even share.** Other builders still may not.
- **Its role tells it** to grep for placeholders after each sync and fill every one to the owner's answers before it stops.
- Unit tests in `tests/test_claims.sh`: it can; another builder still cannot.
- **Disclosed:** `dev90` also carries Gate 89's interview change (no business decisions, no interview).
  - On Tiny Shop's business goal its planner still found 14–19 decisions in 3 of 3 calls (Gate 89's planner check), so the interview runs as before.

## Setup

- **Gate 85's five live flights, unchanged otherwise** (Hive's own reader on the default model), with the merged code.
- Driver `referee/flight90.py`, analysis `referee/analyze.py` (compares with Gate 85), committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| J1 | No delivered build has a placeholder left in `shop/*.py` (all five) | 75% |
| J2 | pass^1 ≥ 0.8 | 60% |
| J3 | Median hidden ≥ 26 of 27 | 65% |
| J4 | Median owner prompts ≤ 1.2× Gate 85's | 75% |

## Decision rules

- **Claim (J1, J2 and J3):** the fix stays on main. Gate 91 then tests Haiku for Hive's own reading against these flights.
- **J1 fails:** read how the placeholder survived, and fix that path.

## Limits

- Five flights against five, with a synthetic owner. About $25.
