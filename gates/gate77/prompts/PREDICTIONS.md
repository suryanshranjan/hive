# Gate 77 predictions: split the night builders too?

Registered Nov 1 2026, before the flights. The user is away for a day: "whatever is necessary".

## Why this test

- **Gate 76:** the shipped flow flew. Live it scored 27 of 27, with the split engaged. The overnight flight scored only 22 of 27 after `hive morning`.
- **The overnight misses** were decisions no night builder thought to record: 4 changed-mind refund windows and 1 points case. Its 16 questions came from two of the three builders, scattered.
- **Overnight has no split.** Gate 74's split fixed the same symptom live: one builder owns the owner's decisions and asks systematically, and the business rules went from 3–7 points behind one agent to 2.6 ahead.
- **This gate:** does the same split, with the business builder *recording* systematically for the morning, raise the overnight score, without flooding the owner's morning?

## Setup

- **The job, owner and score:** Gate 76's. Tiny Shop's three-part goal; the private policy and 27 hidden acceptance tests in `private/g54`; the synthetic owner (Gate 54's brief) answers every prompt, including each morning question.
- **Product change under test** (`hive/swarm.py`, behind `HIVE_SPLIT_OVERNIGHT=1`, off by default):
  - with 3 or more night builders, the last is the business builder: it records the owner's questions systematically, part by part (the rule, rounding and form, boundaries, bad input), then builds its best guess and encodes it as a test;
  - the others build the rest and record nothing.
- **Arms**, each run with `hive start --overnight` then `hive morning`, from an empty `~/.hive`:
  - **control:** as shipped;
  - **split:** `HIVE_SPLIT_OVERNIGHT=1`.
- **Three flights per arm,** alternating: control1, split1, control2, split2, control3, split3.
- **Measures:** hidden tests passed after the morning (and at night); questions recorded overnight (the owner's morning load).
- Driver `referee/flight77.py` (Gate 76's), analysis `referee/analyze.py`, both committed now.
- Gate 76's overnight flight (22 of 27, 16 questions) is not counted in either arm.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| N1 | Split's mean after the morning ≥ control's + 2 (of 27) | 45% |
| N2 | In every split flight the split engages and only the business builder records | 70% |
| N3 | Split's mean questions recorded ≤ 1.5× control's | 65% |
| N4 | No crash; the morning fix runs in all six flights | 85% |

## Decision rules

- **Claim (N1 and N3):** the overnight split ships as the default.
- **If N1 fails:** the overnight path stays as it is. The next candidate is a short interview before the owner leaves: he is at the keyboard when he types `hive start --overnight`.
- **If N3 fails but N1 holds:** the split's morning load is too heavy to ship as is; measure his morning minutes before deciding.

## Limits

- Three flights per arm, on one small project, with a synthetic owner whose answers never drift. The hidden tests were written in Gate 54 and are reused.
- About $12 and about an hour.
