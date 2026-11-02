# Gate 103 predictions: the owner's own examples as checks before delivery

Registered Nov 2 2026, before any replay or flight.

## Why this test

Gate 101's two failed flights without memory were not missed decisions. The owner's new rule was given, but never reached the code the product runs:
- **F1 (20 of 29):** on the code sheet he corrected seven points rules to the new rate (1 point per ₹50). One change builder got all seventeen corrections in its prompt and changed only the refund rules. Hive then told him: "Your changes are in, and every test passes."
- **F3 (17 of 29):** he stated the new rate in the interview. The builder wrote it in a new `shop/points.py` that nothing calls, and left `shop/loyalty.points_earned` at the old rate.

The builders' own tests passed both times: they test what the builder wrote, not the owner's examples through the product's own functions.

This is MAST's verification failure (FM-3.2/3.3). The remedy MAST reports is a check against the task's own objective. Here, that is the owner's examples, which are already in his words ("₹500 earns 10").

## The change (branch `dev103`, `hive/examples.py`)

Before delivery, one coding agent works in a throwaway copy of the build. For each of the owner's rules with a concrete example:
- it writes a test calling the function the product already uses;
- it runs the test;
- it reports the examples that fail.

A failure sends one builder back with those examples, then delivery.

## 103a: the wind tunnel (replay, no flights)

- **What:** the check runs on the 32 delivered Tiny Shop builds kept from Gates 95–99 and 101, with each build's own rules: interview, hand-over, his answers and his corrections.
- **Failed flights (5):**
  - Gate 97 live1, 15/27 (a refund result shape);
  - Gate 99 overnight2, 23/27, and overnight5, 21/27 (missed decisions);
  - Gate 101 F1, 20/29, and F3, 17/29.
- **Scripts:** `referee/replay103.py` and `referee/analyze103a.py`, committed now.

| # | Prediction | Odds |
| --- | --- | --- |
| R1 | F1 and F3 are both flagged | 70% |
| R2 | At most 20% of good flights (hidden ≥ total − 1) are flagged: false alarms, each costing a fix round | 50% |
| R3 | At least 3 of the 5 failed flights are flagged | 45% (Gate 99's misses are decisions nobody asked, so no example exists) |
| R4 | Mean cost of a check ≤ $0.40 | 55% |

**Decision rules:**
- **R1 and R2 hold:** fly it (103b).
- **R2 fails:** read the false alarms and tighten the brief before any flight.
- **R1 fails:** the check cannot see this failure; drop it.

## 103b: flights (registered here, run only if 103a passes)

- **Arms:**
  - Gate 101's F arm (day 2, no memory, silent drift), 3 flights with the check;
  - 3 live Tiny Shop flights (Gate 98's setup), to check that pass^k holds.

| # | Prediction | Odds |
| --- | --- | --- |
| X1 | F-with-check median hidden ≥ 26 of 29 (Gate 101 F: 20) | 55% |
| X2 | The live flights all ≥ 24 of 27 | 75% |
| X3 | The check adds ≤ $0.60 and ≤ 4 minutes a flight | 60% |

**Decision rule:**
- **X1 and X2 hold:** ships.

## Limits

- One project and a synthetic owner.
- The replay judges the check on builds made without it, so it shows whether the check sees a failure, not whether the fix round repairs it (103b tests that).
- About $10 for 103a and $15 for 103b.

## 103a2: the checker sees the product as it was before the build (registered after 103a, before its replay)

- **What 103a showed:**
  - F1 flagged (12 points examples fail), F3 not: its checker tested the builder's new, unused `shop/points.py` and a new `refund_return`, because the builder's new tests call them.
  - 2 of 23 good flights flagged, both true deviations from the owner's rounding words that the hidden tests do not cover.
  - Mean cost $0.11.
- **The change:**
  - the checker gets a copy of the product before the build (the `source` clone Hive already keeps);
  - it tests, in this order, a function the goal names, else one that existed before, and only then a new one.
- **Same 32 builds:** `replay103.py --v2`, `analyze103a.py --v2`.

| # | Prediction | Odds |
| --- | --- | --- |
| R1' | F1 and F3 both flagged | 70% |
| R2' | ≤ 20% of good flights flagged | 60% |
| R4' | Mean cost ≤ $0.40 | 80% |

**Decision rule:** R1' and R2' hold → 103b flights.
