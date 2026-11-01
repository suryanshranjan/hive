# Gate 88 predictions: a handful of spot checks, not 12–32 (Gap 2)

Registered Nov 2 2026, before the flights.

## Why this test

- **Gate 85:** the median flight put 55 prompts to the owner. The interview took 14–19 of them, and the review's spot checks most of the rest (12–32 "Right?" cases per flight).
- **A founder wants under 10 minutes** (`docs/gap_plan.md`, Gap 2).
- **Spot checks earn their place.** Gate 63: spot-checking every part, the ones his review left alone first, gave +7.6 hidden points. Ambig-SWE: many detailed questions overwhelm users.
- **So keep every part, but show only a handful:** at most 6 spot checks, round-robin across the parts in Gate 63's order, with each part's most important case first (`hive/spotcheck.py` `pick`; `HIVE_SPOT_MAX`).

## Setup

- **Gate 85's five live flights, with one change:** `HIVE_SPOT_MAX=6`.
- Hive's own reader is pinned to Gate 85's (the CLI's default model), whatever Gate 87 ships.
- Same project, private policy, 27 hidden tests and synthetic owner.
- Driver `referee/flight88.py`, analysis `referee/analyze.py` (compares with Gate 85), committed now.
- **Order:** after Gate 87.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| L1 | Median owner prompts ≤ 0.7× Gate 85's (≤ 38) | 70% |
| L2 | pass^1 ≥ 0.8 (no drop) | 55% |
| L3 | Median hidden ≥ 26 of 27 | 60% |
| L4 | Hive's own spend ≤ 0.85× Gate 85's | 60% |

## Decision rules

- **Claim (L1, L2 and L3):** at most 6 spot checks by default.
- **L1 holds but L2 or L3 fails:** the extra checks were catching errors. Find which part's errors went through and rank by stakes, not by part.

## Limits

- Five flights against five, on one small project, with a synthetic owner who answers every check carefully.
- About $15.
