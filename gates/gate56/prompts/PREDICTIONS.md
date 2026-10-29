# Gate 56 predictions: a short sheet for the skimming owner

Registered Oct 30 2026, before the run. Overnight. Gate 45 and the founder's Telegram are untouched.

## Why this test

Gate 55: on an 83-rule code sheet, a skimming owner repaired 5 to 6 of 19 wrong decisions, whether he read a list or Jarvis's conversation; a careful owner repaired 19 of 19. Its registered rule for this outcome: the next lever is fewer, sharper things to read. Of 83 rules only 25 carried the owner's decisions. The rest were mechanics: NULL in gives NULL out, numbers given as text, extra spaces.

The change under test: a describer that writes only the **business choices** the code made (amounts, cut-offs, rounding, caps, what happens in each business situation, and surprising input handling), at most 30 rules, each with one example (`prompts/describer_short_brief.md`). The risk is that it leaves out decisions that live in input handling ("an impossible date gives n/a").

## Setup

- **Rules:** Gate 55's rule set (published after its scoring; the builders never see it), with a new hidden draw (seed 56200000) and a new visible draw (56100).
- **Stage 1:** a fresh N0 build (3 builders). From its code, two describers write:
  - **D:** in full (Gate 55's brief);
  - **DS:** business choices only.
- **Two separate reviews by the same skimming owner** (Gate 55's brief and policy prose; a terminal rule list, `interview.confirm_sheet`):
  - **SF** from D;
  - **SS** from DS.
- **Stage 2:** fresh builders from SF and SS (3 each).
- **Judge:** labels D, DS, SF, SS and R per declared decision before stage 2.
- **Driver and analysis:** `referee/review56.py`, `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| T1 | The short sheet has at most 35 rules | 80% |
| T2 | After review, the short sheet states ≥ 15 more points of the 25 decisions right than the full one | 50% |
| T3 | Hidden pass SS ≥ SF + 5 | 45% |
| T4 | Before review, the short sheet addresses ≥ 70% of the decisions | 50% |

## Decision rules

- **Ship:** T2 and T3 hold. The describer writes the short sheet by default, with the full one a tap away.
- **Kill:** SS is no better on hidden pass or decisions. Then a skimmer's ceiling is about a quarter of the wrong rules however they are shown, and the product's next step is getting the owner's careful attention (when and how he is asked), not the sheet.

## Limits

- One run per arm, synthetic skimming owner. About $7.
