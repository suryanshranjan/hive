# Gate 84 predictions: check the goal's stated interfaces when the review is skipped

Registered Nov 1 2026, before any run. The user: "Go on".

## Why this test

- **Gate 83 lost 13 of 27 hidden tests to one thing.** After an owner answer about mixed payments, the business builder added `card` and `store_credit` keys to `refund()`'s result. The goal had fixed that result as exactly `{'amount': …, 'method': …}`.
- **Nothing caught it.** The builders had asked 3 questions, so Gate 68's rule skipped the review.
- **The new check (`hive/contract.py`, wired into `hive start` where the review is skipped):**
  1. one model call reads the interfaces the goal states: file, function, arguments, and a dict result's keys;
  2. the delivered code is checked against them from its syntax: a function missing, arguments renamed, a returned dict literal with other keys;
  3. if anything differs, one builder puts it back.

  It costs the owner nothing. `HIVE_CONTRACT_CHECK=0` turns it off.

## Disclosed before running

- The check was written while looking at Gate 83's failure and was tried on the 8 delivered builds of Gates 76 and 81–83. It flagged Gate 83's live `refund()` (extra: `card`, `store_credit`) and none of the other 7.
- That is how it was developed, not a prediction, so it is not scored here.
- Unit tests (`tests/test_assistant.py`): extra keys and a missing function are found; matching code, and a result not written as a plain dict literal, are left alone.

## Setup

- **Part A** (`referee/fix84.py`): a copy of Gate 83's live build state. The product's `_keep_contract` runs on it: the check, then the fix round. The hidden suite (`private/g54`) is scored before and after, and the fixed code is re-checked.
- **Part B** (`referee/flight84.py`, Gate 83's driver): two live flights of `hive start` with the check in place, `live1` then `live2`. Tiny Shop, the private policy and 27 hidden tests, and the synthetic owner.
- Analysis `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| I1 | Gate 83's build: the check finds the extra keys, the fix round runs, the fixed code has 0 problems, and ≥ 24 of 27 hidden pass | 65% |
| I3 | Both flights: no crash, one branch, ≥ 24 of 27 | 60% |
| I4 | Both flights: the delivered code has 0 interface problems (re-checked by the referee with its own call reading the goal) | 80% |
| I5 | Both flights: where the review was skipped, the check ran, and its fix round ran if it found anything | 85% |

## Decision rules

- **I1, I4 and I5 hold:** the check stays on (it is on now).
- **I1 fails because the fix breaks behaviour:** the fix note is wrong; rework it.
- **The check finds problems in code the referee scores as right:** it cries wolf. Narrow it, or turn it off.

## Limits

- One repaired build and two flights, on one small project, with a synthetic owner.
- The check covers only what a goal states outright, and only dict results written as literals.
- About $8.
