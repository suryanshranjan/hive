# Gate 95 predictions: show the ordinary case first

Registered Nov 2 2026, before the flights.

## Why this test

- **Gate 93, the new baseline:** pass^1 0.80, and pass^5 fails on one flight in five.
- **The failures that break it are a family:**
  - state kept between calls (Gate 85);
  - a result's form changed (Gates 83, 90);
  - an owner's rule built with an unsafe new default: `delivered: bool = False`, so every ordinary refund became 0 (Gate 93).
- **Each passes the builders' tests and the owner's review, and each shows in the most ordinary case.**
- **The spot-check finder never leads with that case.** Its brief asks for "choices the owner might not expect", so Gate 93's live1 opened with "a cancelled order marked damaged", and no plain refund was shown.

## The change (branch `dev95`; merged after Gates 94 and 92 finish)

- The spot-check brief: "the first check of every part is its most ordinary case: a typical customer, a typical amount, nothing unusual, built the way the rest of the product already builds it".
- With at most 6 checks, round-robin across the parts (Gate 88), each part's ordinary case is shown first.

## Setup

- Gate 93's five live flights, on main after the merge.
- Driver `referee/flight95.py`, analysis `referee/analyze.py` (Gate 93's, with C3's bound set to ≤ 38), committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| C1 | pass^1 ≥ 0.8 | 70% |
| C2 | pass^5 (all five succeed) | 40% |
| C3 | Median owner prompts ≤ 38 | 65% |
| C4 | No delivery breaks a stated interface | 85% |

## Decision rules

- **Claim (C2 and C3):** the ordinary case first ships.
- **C2 fails:** read the failing flight. If its ordinary case was shown and the owner let it pass, the synthetic owner, not the check, is the limit. If it was not shown, the finder ignored the brief.

## Limits

- Five flights cannot show a reliability gain with confidence (Gate 93 was 4 of 5). This is a first look. About $25.
