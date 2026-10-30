# Gate 57 predictions: spot checks for the skimming owner

Registered Oct 30 2026, before the run. Asked for by the user ("Test it"). Gate 45 and the founder's Telegram are untouched; this is the wind-tunnel version, before any test with him.

## Why this test

Gates 55–56: a skimming owner repaired about a quarter of the code sheet's wrong decisions, whether he read a list, Jarvis's conversation or a short sheet. He corrected what he remembered and let details pass. Gate 38 suggested the founder decides when he sees a **concrete outcome**. So try showing outcomes, not rules:
- Hive runs the built code on up to 30 concrete cases where it made a non-obvious choice: boundaries, rounding, caps, business situations, odd inputs that matter.
- He sees them one at a time, in business words: "Ravi's 100-rupee invoice is paid 31 days late: the late fee comes to 2 rupees. Right?"
- He presses Enter, or says what should happen.
- His corrections are then applied to the rule sheet by one model call (`prompts/apply_brief.md`).

A wrong detail in a rule ("the fee is rounded to the cent") is easy to skim past. The same detail as a number in a case ("…comes to 12.37 rupees") may be harder to miss.

## Setup

- **Rules:** Gate 55's rule set (published; builders never see it), new visible and hidden draws (seeds 57100, 57200000).
- **Stage 1:** a fresh N0 build. From its code (never the oracle):
  - the describer writes D (Gate 55's brief);
  - a spotter runs the code on up to 30 concrete cases (`prompts/spotter_brief.md`).
- **Two separate sessions with the same skimming owner** (Gate 55's brief and policy prose):
  - **SL:** D as a rule list (`interview.confirm_sheet`, as Gates 55–56);
  - **SP:** the spot checks, one at a time, his corrections applied to D.
- **Stage 2:** fresh builders from SL and SP (3 each).
- **Judge:** labels D, SL, SP and R per declared decision before stage 2.
- **Driver and analysis:** `referee/review57.py`, `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| U1 | After review, SP states ≥ 15 points more of the 25 decisions right than SL | 45% |
| U2 | Hidden pass SP ≥ SL + 5 | 45% |
| U3 | The skimmer corrects ≥ 25% of the spot checks | 55% |
| U4 | Applying his corrections spoils at most 1 decision D had right | 80% |

## Decision rules

- **Ship:** U1 and U2 hold. Spot checks become Hive's review when the owner skims, and are tried with the founder next.
- **Kill:** SP is no better on either. Then a skimmer's gain is capped at what he remembers, however it is shown, and Hive should fill the rest from his documents and earlier rulings.

## Limits

- One run per arm, a synthetic skimmer. About $7.
