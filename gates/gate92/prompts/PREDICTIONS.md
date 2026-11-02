# Gate 92 predictions: when the owner changes his mind (Gap 5)

Registered Nov 2 2026, before any flight.

## Why this test

- **Real owners drift.** Gate 38: the founder's confirmed rules matched his own next-day verdicts on only 2 of 11.
- **Hive's memory works against drift.** It keeps every ruling in `~/.hive/rules/<project>.json` and tells the next build's builders to follow them and "not ask about them again". The interview also skips anything already ruled on.
- **The question:** when his rules change and he says so, does Hive's memory make the old rules stick? Nothing has tested this.

## Setup

- **Day 1:** one live flight of `hive start` as shipped (Gate 90's flow): Tiny Shop's three-part goal, the owner's day-1 policy (`private/g54`), and the synthetic owner. He merges the delivered branch, and Hive's state after day 1 (its rulings) is kept.
- **Day 2:** his rules have changed (`private/g92/policy_day2.md`):
  - the full-refund window is 7 days, not 14;
  - the minimum refund is 100 rupees, not 50;
  - a point per 50 rupees, not 100.

  He asks: "Some of my shop's rules have changed. Update refunds and loyalty points so they follow how my shop works now." The synthetic owner answers from the day-2 policy.
- **Arms, 3 day-2 flights each, on the merged day-1 repo:**
  - **M:** Hive's memory of day 1 kept, as a real owner would have it;
  - **F:** no memory (only his fast/cheap choice).
- **Hidden:** 29 cases written from the day-2 policy by an oracle (`private/g92/make_tests.py`, `test_day2.py`). 12 of them differ from the day-1 rules.
- Driver `referee/flight92.py` (Gate 90's, two days), analysis `referee/analyze.py`, committed now. **Order:** after Gate 91.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| D1 | F's median ≥ 26 of 29 | 55% |
| D2 | M's median ≤ F's − 5 (the old rulings win over his new word) | 50% |
| D3 | M asks fewer prompts than F (median) | 70% |

## Decision rules

- **D2 holds:** memory makes drift sticky. The fix: rulings that touch the goal's parts are put to him again, as "still true?", whenever he says rules have changed, and his latest word replaces the old ruling. Test it in the next gate.
- **D2 fails:** the builders follow his new word over the old rulings. Memory is safe under drift, as far as this test shows.

## Limits

- One day-1 build; 3 flights per arm on day 2; a synthetic owner who changes exactly 3 rules and states the change.
- About $20.
