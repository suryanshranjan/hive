# Gate 64 predictions: dynamic effort (a strong planner over cheap builders, escalation when stuck)

Registered Oct 30 2026, before any team runs. Asked for by the user: "orchestrator better agent then worker lesser capable agent … one follows the already planned direction … dynamically increase effort as required". No owner, no Telegram.

## Why this test

- **Gate 62's side result:** on intent-bound jobs, Haiku builders passed as many hidden checks as Sonnet or Opus, for about a sixth of Sonnet's cost.
- **What is untested:** whether cheap builders can do hard engineering, such as building an engine from a skeleton.
- **The user's idea, in two parts:**
  1. **A planner:** a strong model plans, so weaker builders follow a direction instead of finding one.
  2. **Escalation:** effort rises only where the work gets stuck.
- **Gate 46 is not the answer to part 1.** Its lead planned for builders of the same strength as itself, who did not need a plan (the lead lost: 1.2× slower). A plan may be worth more to weaker builders.

## Setup

- **Project:** Gate 46's deep project, from a 221-line skeleton to 1,340 visible tests. The hidden suite is Gate 50's (`private/g43/hidden2`).
- **Teams:** 4 builders each. Each team runs alone on the 2-CPU machine, in the order H, OHE, S, HE, OH.
- **Time cap:** every wave's builders stop after 30 minutes. Gate 50's 4 Sonnet builders took 6.2 minutes to 95%.

| Team | Who builds |
| --- | --- |
| **S** | 4 Sonnet builders, flat (today's Hive) |
| **H** | 4 Haiku builders, flat |
| **OH** | An Opus lead writes and keeps BRAIN.md (Gate 46's lead prompt) over 4 Haiku builders who follow it |
| **HE** | H, then **escalation**: if any visible test still fails when the Haiku builders stop, 2 Sonnet builders take over what is left; if anything still fails, 1 Opus builder. Locks left behind are cleared first |
| **OHE** | OH, then the same escalation. The lead keeps running during it |

- **Measures:**
  - minutes to 95% and to 100% of visible tests;
  - the cost of every builder in every wave, plus the lead;
  - hidden pass;
  - breaks of main.
- Driver `referee/run64.py`, analysis `referee/analyze.py`, both committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| D1 | H (Haiku alone) reaches 1,340 visible | 40% |
| D2 | OH reaches 95% in at most 0.8× H's time (or H never does) | 45% |
| D3 | HE finishes, hidden within 1 point of S, at ≤ 0.6× S's cost | 40% |
| D4 | OHE the same | 35% |
| D5 | OHE costs at least as much as HE (the Opus plan does not pay for itself) | 55% |

## Decision rules

- **Cheap pace becomes Haiku plus escalation:** D3 holds. `hive pace cheap` would use Haiku builders, and stronger builders only for what is left.
- **Add the Opus planner:** only if D4 holds and OHE beats HE by ≥ 15% on cost or on time to finish.
- **Kill:** neither HE nor OHE finishes at ≤ 0.6× S's cost. Sonnet builders stay.

## Limits

- One run per team. Gate 46's two identical teams differed by about 30% in time, so only large time differences count.
- Escalation builders get the flat prompt, which describes the skeleton's starting state. They see the real state at their first sync.
- About $25.
