# Gate 16 results: the stacked interface (handbook + extracted tour + questions), Oct 27 2026

**Question.** Gate 15's handbook-derived tour reached 80.6% hidden, short of the owner's own tour (92.6%) at decisions nobody wrote down. Does stacking everything a documented owner can give (the handbook, the extracted tour and builder questions) close that gap?

**Answer.**
- **Each layer added, but the stack fell short of its target.** Hidden correctness: nothing 41.4%, extracted tour **60.8%**, plus handbook **71.0%**, plus 17 questions **83.2%**. S2, S3, S6 and S7 held; S1 (90%), S4 (replication) and S5 (closing the floor) failed.
- **The extracted tour was much weaker than in Gate 15** (+19.4 points against +36.0). A third of the extractor's picks (17 of 50) were exact hidden-test inputs and were removed by the copy rule. That rule penalizes the extractor for pointing exactly where the owner's own QA points; it is a flaw in the lab's design, fixed below.
- **Documents can mislead on what they leave out.** The handbook said Net Promoter categories "follow the standard". Builders inferred that fractional scores are invalid, but the unwritten rule rounds them. With the handbook, `nps_category` went from 15 errors fixed to 0.
- **The unwritten-decision floor shrank but did not close:** the full stack fixed 0.79 of N0's edge errors on functions with an omitted decision, against 0.83 elsewhere.

## Setup

- **Rules and extractor.** A fresh independent rule-giver with Gate 15's brief: 20 decisions clear, 15 vague, 15 omitted in the handbook, exactly as required. The extractor ($0.24) saw only the handbook and spec and picked 50 inputs; 17 were exact TYPICAL or EDGE inputs and were dropped, leaving 33 (20 visible tests). Predictions and analysis code were pushed before the rules existed (commit 7d04573).
- **Teams** (3 builders each): **N0**; **X** (extracted tour); **HX** (handbook + extracted tour); **HXQ** (handbook + extracted tour + 17 questions for the team).
- **Hidden suite.** 500 tests (seed 16200000), 70% edge calls. Not committed.

| Team | Gets | Builder cost | Visible | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | nothing | $1.88 | 1,380/1,380 | **207/500 (41.4%)** | 31.0–53.4% | |
| X | extracted tour (33) | $2.46 | 1,400/1,400 | **304/500 (60.8%)** | 49.4–72.4% | +19.4 (CI +6.0 to +32.2) |
| HX | + handbook | $2.06 | 1,400/1,400 | **355/500 (71.0%)** | 62.0–80.2% | +29.6 (CI +16.4 to +41.4) |
| HXQ | + 17 questions (17 used) | $2.31 | 1,400/1,400 | **416/500 (83.2%)** | 73.2–91.8% | +41.8 (CI +28.4 to +54.6) |

Rule-giver $1.23, extractor $0.24; total $10.18 at list price.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| S1 | HXQ ≥ 90% | **Failed**: 83.2% |
| S2 | HX − X ≥ +3 | **Held**: +10.2 (CI −1.6 to +23.2) |
| S3 | HXQ − HX ≥ +3 | **Held**: +12.2 (CI +3.4 to +21.8) |
| S4 | X − N0 ≥ +25 | **Failed**: +19.4 (CI +6.2 to +32.4) |
| S5 | HXQ fixes ≥ 0.85 on functions with an omitted decision | **Failed**: 0.79 (X 0.50, HX 0.66) |
| S6 | HXQ uses ≥ 15 of 17; visible tests pass | **Held**: 17 of 17; all pass |
| S7 | N0 below 70% | **Held**: 41.4% |
| Kill | HXQ < 85% and HXQ ≤ HX | **Did not fire** (HXQ is 12.2 above HX) |
| Rule | S2 fails: drop the handbook from the stack | **Did not fire** |

## What it means

### 1. The layers add, roughly independently

| Layer added | Gain (points) | Gate |
| --- | --- | --- |
| Extracted tour | +19.4 (Gate 15: +36.0) | 16 (15) |
| Handbook on top of it | +10.2 | 16 |
| 17 builder questions on top of both | +12.2 | 16 |
| Builder questions on top of the owner's tour | +5.8 | 13 |

Questions bought more on top of documents (+12.2) than on top of the owner's full tour (+5.8): they fill what the documents leave, and there is more left.

### 2. The copy rule mismeasures the extractor (a lab flaw, now found)

The registered rule drops any extractor pick that equals a hidden-suite input, so no hidden test leaks into a tour. It dropped 14 of 50 picks in Gate 15 and 17 here. Those were the extractor's best picks: the same inputs the owner's own QA list chose. The owner's tour was written to avoid the list; the extractor could not see it. So X has been underestimated twice, and by more when the extractor is better aligned with the owner.

**Design change for the lab:** keep every extractor pick in the tour, and remove matching calls from the *hidden suite* for all teams. No leakage, and no penalty for good targeting. The same rule should apply to any arm whose examples are not chosen with the hidden list in view.

### 3. Silent-but-authoritative documents mislead

| Function | Omitted decision | Handbook | X fixed | HX fixed |
| --- | --- | --- | --- | --- |
| nps_category | fractional scores rounded, halves up | "Net Promoter categories follow the standard published…" | 15 / 28 | **0** / 28 |

With the handbook, builders treated `6.5` as invalid (NULL). Without it, they guessed a rounding direction and got 15 calls right. A document that sounds complete makes builders more confident about exactly the things it does not say. Gate 7 saw the reverse problem: documents overturned the owner. Documents and owners each have gaps, and they differ.

### 4. Where the stack stands

| Owner has | Best measured interface | Hidden pass |
| --- | --- | --- |
| A list of their own decisions | owner's tour + questions | 95.2% (Gate 13); tour alone 89.4–95.6% (Gates 13–15) |
| Documents only | handbook + extracted tour + questions | 83.2% (Gate 16); extracted tour alone 60.8–80.6% (Gates 15–16) |
| Nothing written | builder questions only | 67.2–81.6% (Gates 12, 13) |

## Design consequences for Hive's intent interface

1. **Owner with documents:** ship the handbook, the owner-answered extracted examples and builder questions together. Each layer added here.
2. **Prefer a decision list from the owner when it can be had.** It beat documents by about 10 to 12 points in both gates that compared them (15: 92.6 against 80.6; 16's stack 83.2 against Gates 13–15's tours).
3. **Treat a document's silence as unknown, not as "standard".** Builder prompts should say so, and extractors should probe every place a document waves at "the standard" or "usual practice".
4. **Lab:** fix the copy rule as above before measuring extracted tours again.

## Honest odds

- With the fair copy rule, the extracted tour alone gains ≥ +30 points on a new rule set: about 60%.
- The stack reaches 90% with the fair copy rule plus a "silence is unknown" prompt: about 50%.

## Limits

- One run per team. The extracted tour's gain varied from +36 to +19 across two gates, so its true size is uncertain.
- Handbooks were written by the same agent that wrote the rules, told how much to leave out.
- Extractor, rule-giver and builders are the same kind of model.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions and decision rules, pushed before the rules existed (briefs reused from `gates/gate15/prompts/`) |
| `referee/analyze.py` | Registered analysis (committed before the run) |
| `referee/oracle.py` | Rules, decisions, tour, handbook and status, unsealed after scoring (synthetic) |
| `results/xtour_inputs.json`, `results/extractor/` | The extractor's picks (kept and dropped) and raw output |
| `results/` | Summary, analysis output, every question and answer, probes, cost per worker, run log, rule-giver output |
| `swarms/*.bundle`, `logs/` | All four teams' histories; worker logs |
