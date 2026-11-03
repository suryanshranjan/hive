# Gate 103 results: the owner's own examples as checks before delivery

*103a, 103a2 and 103b are done. The owner's-examples check ships (merged as `62ddaed`, on by default).*

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

## 103b: flights (Nov 2–3 2026): ships

**Answer.** X1 and X2 held, so by the registered rule the owner's-examples check ships: it runs before every delivery, on by default (`HIVE_EXAMPLE_CHECK=0` turns it off). X3 failed on minutes (cost held); see below.

| Flight | Hidden | Prompts | Minutes | Check | Fix round |
| --- | --- | --- | --- | --- | --- |
| Drift F1 (Gate 101's F arm: no memory, silent drift) | **29 / 29** | 49 | 15.4 | $0.27 (2 runs) | 1 ($0.12) |
| Drift F2 | **29 / 29** | 31 | 9.4 | $0.11 | none |
| Drift F3 | not flown (see below) | | | | |
| Live 1 | **26 / 27** | 28 | 80.7 (stalled; see below) | $0.25 | none |
| Live 2 | **27 / 27** | 28 | 15.0 | $0.32 | 1 ($0.37) |
| Live 3 | **27 / 27** | 41 | 17.5 | $0.49 | none |

**Predictions scored** (`referee/analyze103b.py`; output in `results/analysis_103b.txt`):

| # | Prediction | Result |
| --- | --- | --- |
| X1 | Drift F with the check, median hidden ≥ 26 of 29 | **Held:** 29 (Gate 101 F without it: 20) |
| X2 | Every live flight ≥ 24 of 27 | **Held:** 26, 27, 27 |
| X3 | The check adds ≤ $0.60 and ≤ 4 minutes a flight | **Failed on minutes.** The check and its fix rounds cost $0.36 a flight (held). The median live flight took 17.5 minutes against Gate 98's 6.2 (+11.3) |

**What the check caught:**
- **Drift F1:** the old points rate. The owner's example of ₹1,500 earning 30 points failed in `shop/loyalty.points_earned`; one builder fixed it, and the build reached 29 of 29.
- **Live 2:** split payments. The built `refund()` sent a ₹1,500 refund paid ₹1,000 by card and ₹500 by store credit entirely to the card. The owner's examples ("Rs 1,000 to her card and Rs 500 as store credit") failed. One fix round ($0.37) put it right, and the flight ended 27 of 27.
- In the other flights nothing was flagged, and nothing was flagged wrongly.

**Why X3's minutes are not clean (disclosed):**
- **A different machine.** The live flights ran on the user's laptop, in the Docker lab container (Nov 3); Gate 98's were on the cloud lab machine.
- **Live 1 stalled.** Two builders sat idle for about an hour between commands: w3's own report says "about 65 minutes, mostly long gaps", against 2 minutes of model time. This was the same window in which the laptop ran critically low on memory, low enough that Claude Code stopped background tasks twice.
- **Even so,** live 2 and 3 took 15.0 and 17.5 minutes, against 4–10 for Gate 98. Live 2 included its fix round. So part of the +11.3 is the check's own fix rounds and part is the slower machine; this gate cannot separate the two.
- **The first launch of live 1 was stopped and rerun from scratch:** the clean home folder's copy of the Claude login expired mid-flight. The rerun read the laptop's live login.

**Drift F3 was not flown.** It needs the day-2 policy, the hidden tests (`private/g92`) and Gate 101's day-1 state, which exist only on the cloud lab machine. X1 is decided without it: with F1 and F2 at 29, the median of three is 29 whatever F3 scores.

## Files

`referee/` (`replay103.py`, `analyze103a.py`, `flight103_drift.py`, `flight103_live.py`, `analyze103b.py`); `results/` (replays, drift F1–F2, live 1–3: flight records, owner logs, terminals, run logs and what the check flagged; `analysis_103b.txt`).

`results/`:
- `replay_v1/` and `replay_v2/`, one JSON per build;
- `drift_F1/` and `drift_F2/`: the terminal, prompts, scores, the check's report and the run log;
- `analysis_103a.txt` and `analysis_103a2.txt`.
