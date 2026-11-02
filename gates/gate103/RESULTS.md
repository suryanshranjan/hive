# Gate 103 results: the owner's own examples as checks before delivery

*103a and 103a2 (the wind tunnel) are done. 103b (flights): 2 of 6 flown, with dev103 merged on main under test (`62ddaed`).*

**Question.** Gate 101's two failures without memory were verification failures: the owner's new rule was given, but never reached the function the product runs. Can one cheap check before delivery see this, without crying wolf on good builds? The check runs the owner's own examples through the product's own functions.

## 103a: replay on 32 stored builds, first brief (Nov 2 2026)

- **Flagged:** F1 (12 points examples fail) and 1 of the other 4 failed flights.
- **Not flagged: F3.** Its checker tested the builder's new `shop/points.py` and a new `refund_return`, which nothing calls, because the builder's new tests call them.
- **Good flights flagged:** 2 of 23. Both are true deviations from the owner's rounding words that the hidden tests do not cover (Gate 95 live2: refunds ₹1,250 where he said ₹1,249; Gate 98 live2: 7 points where he said 6).
- **Cost:** a mean of $0.11 a check, about 1–2 minutes.

| # | Prediction | Result |
| --- | --- | --- |
| R1 | F1 and F3 both flagged | **Failed:** F3 not flagged |
| R2 | ≤ 20% of good flights flagged | **Held:** 2 of 23 |
| R3 | ≥ 3 of 5 failed flights flagged | **Failed:** 1 |
| R4 | Mean cost ≤ $0.40 | **Held:** $0.11 |

## 103a2: the checker also sees the product before the build (registered after 103a)

The change: test, in this order, a function the goal names, else one that existed before the build, and only then a new one.

- **Flagged:** F1 (12 examples) and F3 (5 examples). F3's flags were:
  - the 7-day window ("day 8 gets ₹1,000", got ₹2,000);
  - the point per ₹50 (14 points, got 7);
  - the ₹100 minimum;
  - rounding.
- **Not flagged:**
  - Gate 97 live1, a result-shape failure (the interface check already catches it);
  - Gate 99 overnight2 and overnight5, decisions nobody asked about, so the owner gave no example.
- **Good flights flagged:** 1 of 23 (Gate 95 live2's rounding, a true deviation).
- **Cost:** a mean of $0.11.

| # | Prediction | Result |
| --- | --- | --- |
| R1' | F1 and F3 both flagged | **Held** |
| R2' | ≤ 20% of good flights flagged | **Held:** 1 of 23 |
| R4' | Mean cost ≤ $0.40 | **Held:** $0.11 |
| (R3, same measure) | ≥ 3 of 5 failed flights flagged | 2 of 5: the other three are not this kind of failure |

**Decision:** fly it (103b). dev103 merges after Gate 102 finishes.

**What the check can and cannot see:**
- It sees a rule that the owner gave with an example but that did not reach the product's function.
- It cannot see a decision nobody asked him about (Gate 99) or a changed result shape (Gate 84's check covers that).

## 103b: flights (partial, Nov 2 2026, 23:30 IST)

| Flight | Hidden | Prompts | Minutes | Check | Fix round |
| --- | --- | --- | --- | --- | --- |
| Drift F1 (Gate 101's F arm: no memory, silent drift) | **29 / 29** | 49 | 15.4 | $0.27 (2 runs) | 1 ($0.12) |
| Drift F2 | **29 / 29** | 31 | 9.4 | $0.11 | none |
| Drift F3, live 1–3 | not yet flown | | | | |

- **What happened in F1:**
  - The check found two of the owner's examples failing in `shop/loyalty.points_earned` (₹1,500 should earn 30 points; ₹1,299, 25).
  - One builder fixed the function ("points_earned now 1 per Rs 50"), and the build reached 29 of 29.
  - In Gate 101, the same arm without the check scored 20, 29 and 17.
- **Hive's own spend here ($2.69–4.03)** uses Gate 101's driver, which keeps Gate 85's reader for comparability with Gate 101. It is not the lean reader.
- **The registered scoring** (`referee/analyze103b.py`) is final only after all 6 flights. So far X1 holds (median 29), and X3 holds ($0.25 a flight, +2.1 min). X2 needs the live flights.
- **To finish:**
  1. Run the remaining flights:

     ```
     python3 gates/gate103/referee/flight103_drift.py day2 F 3
     python3 gates/gate103/referee/flight103_live.py live 1
     python3 gates/gate103/referee/flight103_live.py live 2
     python3 gates/gate103/referee/flight103_live.py live 3
     ```

     Each one needs `~/.hive` absent; move it aside after each.
  2. Run `analyze103b.py`.
  3. If X1 and X2 hold, it ships. Otherwise revert `62ddaed`.

## Files

`referee/` (`replay103.py`, `analyze103a.py`, `flight103_drift.py`, `flight103_live.py`, `analyze103b.py`).

`results/`:
- `replay_v1/` and `replay_v2/`, one JSON per build;
- `drift_F1/` and `drift_F2/`: the terminal, prompts, scores, the check's report and the run log;
- `analysis_103a.txt` and `analysis_103a2.txt`.
