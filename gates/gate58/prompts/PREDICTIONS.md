# Gate 58 predictions: the combined review for the skimming owner

Registered Oct 31 2026, before the run. Asked for by the user ("implement the changes and check whatever was the findings"). Gate 45 and the founder's Telegram are untouched; this is the wind-tunnel test, before any test with him.

## Why this test

Gate 57: spot checks drew 17 of 30 corrections from a skimming owner, but the sheet ended no better than the rule list (7 vs 9 of 25 decisions right). Two causes were found:
1. **Conversion:** one model call rewrote the whole sheet from all 17 corrections, and details were lost or contradicted.
2. **Coverage:** 30 cases picked by a spotter left some functions' key choices unshown.

Post hoc, the list and the spot checks caught different decisions (12 of 25 together, against 9 for the list alone). This gate tests the combined review that conjecture suggests, with both losses fixed:
- **CB:** the owner's list review (SL's own), then spot checks covering every function the list left as it was (2 to 5 cases per function, `prompts/spotter_brief.md`).
- **Each correction applied alone,** to the rules about that function only (`prompts/apply_one_brief.md`).
- **Each corrected case worked out again** from the new rules (`prompts/recheck_brief.md`) and shown to him once more ("With your correction: ... Right now?"). A second correction is applied the same way.

## Setup

- **Rules:** Gate 55's published rule set (`gates/gate55/referee/oracle.py`; builders never see it), new visible and hidden draws (seeds 58100, 58200000).
- **Stage 1:** a fresh N0 build. From its code (never the oracle), the describer writes D (Gate 55's brief) and the spotter writes the spot checks.
- **The skimming owner** (Gate 55's brief and policy prose):
  - **SL:** D as a rule list (`interview.confirm_sheet`, as Gates 55–57).
  - **CB:** SL's result, then the spot checks. Starting from SL's own list review isolates what the spot checks add.
- **Stage 2:** fresh builders from SL and CB (3 each).
- **Judge:** labels D, SL, CB and R per declared decision before stage 2.
- **Driver and analysis:** `referee/review58.py`, `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| V1 | CB states ≥ 12 points more of the declared decisions right than SL (about 3 of 25) | 50% |
| V2 | Hidden pass CB ≥ SL + 5 | 45% |
| V3 | Of the corrected cases shown again, ≥ 80% are confirmed as now right | 60% |
| V4 | CB spoils at most 1 decision SL had right | 75% |

## Decision rules

- **Ship:** V1 and V2 hold. The combined review becomes Hive's hand-over for an owner who skims (list, then spot checks with re-show), and is tried with the founder next.
- **Kill:** CB is no better than SL on both. Then a skimmer's gain is capped at what he remembers, however it is shown and confirmed. Hive should rely on his documents and earlier rulings for the rest, and ask a careful review only where the stakes are high.

## Limits

- One run per arm, a synthetic skimmer, one rule set (shared with Gates 55–57).
- About $8.
