# Gate 101 predictions: silent drift

Registered Nov 2 2026, before any flight.

## Why this test

- **Gate 92:** when the owner says his rules changed, Hive's memory is safe. The contradiction check asks "which holds now?" and his latest word wins.
- **Real drift is mostly silent.** Gate 38's founder did not announce that he had changed his mind; his answers simply differed (2 of 11 rules held).
- **The risk:** Hive tells the next build to follow his old rulings and "not ask about them again", and the interview skips anything already ruled on. A silent change may never surface.

## Setup

- Gate 92's design, with two differences:
  - the day-2 goal does not say anything changed: "Customers keep asking about refunds and points on discounted orders. Go over refunds and loyalty points and make sure they handle every case the way my shop works.";
  - the synthetic owner's day-2 policy (`private/g92/policy_day2_silent.md`) is the same three changes with the "(Changed: …)" notes removed, so he never volunteers that anything changed.
- **Day 1:** one live flight, merged. **Day 2:** 3 flights with Hive's day-1 memory (M), 3 without it (F).
- **Hidden:** Gate 92's 29 day-2 cases, 12 of which differ from the day-1 rules.
- Driver `referee/flight101.py`, analysis `referee/analyze.py` (Gate 92's), committed now.
- Runs on main as of registration (`803fecf`).

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| D1 | F's median ≥ 26 of 29 | 55% |
| D2 | M's median ≤ F's − 5 (silent drift sticks when memory is kept) | 50% |
| D3 | M asks fewer prompts than F | 60% |

## Decision rules

- **D2 holds:** memory needs a guard against silent drift. The next change: when a goal touches parts with earlier rulings, show him those rulings as "still true?" in one prompt, instead of telling builders never to ask.
- **D2 fails:** the contradiction check and the review catch silent drift too.

## Limits

One day-1 build; 3 flights per arm; a synthetic owner with exactly 3 changed rules. About $15.
