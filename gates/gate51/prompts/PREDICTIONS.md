# Gate 51 predictions: team notes at 12 builders

Registered Oct 30 2026, before any team runs. Overnight research. Gate 45 and the founder's Telegram are untouched.

## Why this test

Yesterday Hive gained team notes: a one-line message to the team, carried in a landing commit (`hive land --note`), read with `hive notes`. The law switches them on for 10 or more builders, or once a swarm's collisions reach 0.5 per landing. Both thresholds were guesses (BRAIN §7). Talking added nothing at 3 to 7 builders (Gates 43, 44, 46).

Gate 50 found 12 builders *slower* than 7 (6.6 vs 4.2 minutes) at 1.8× the cost. Two explanations compete:
- **The machine:** 12 agent processes on 2 cores.
- **The builders:** crosstalk, which the scalability fit put at κ = 0.013.

Team notes can only help with the second. This gate tests notes exactly where the law turns them on, and samples the machine's load to tell the two apart.

## Setup

- **Project:** Gate 46's deep project (skeleton to 1,340 tests). Hidden suite as in Gate 50.
- **Teams:** 12 builders each, alone on the 2-CPU machine, ABBA: S1, T1, T2, S2.
  - **S:** silent, Gate 50's prompt.
  - **T:** the same, plus team notes:
    - `tools/notes.py` at every sync and before resolving a conflict;
    - `tools/land_note.py` to land with one line for the team when the change matters to others.

    This is Hive's design (notes inside commits), with the gate's tools.
- **Measured:** time to 95% of visible tests, cost, landings, breaks of main, notes posted, hidden pass, and the 1-minute load average every 10 s.
- **Driver and analysis:** `referee/run51.py`, `referee/analyze.py`, committed now.

## Predictions (S and T are each the mean of their two teams)

| # | Prediction | Odds |
| --- | --- | --- |
| F1 | Notes do not make 12 builders ≥ 15% faster | 70% |
| F2 | Cost within ±10% | 65% |
| F3 | The machine is saturated while 12 builders run (mean load ≥ 2.0 on 2 cores) | 60% |
| F4 | Each notes team posts ≥ 5 notes | 60% |

## Decision rules

- **Keep notes at 10+ builders:** notes are ≥ 15% faster in both pairings, at ≤ 1.10× the cost.
- **Turn the size trigger off:** notes are not faster on average. Notes then switch on only when a swarm keeps colliding, and every conflict still shows the recent notes.
- **F3 holds:** the machine, not crosstalk, slows 12 builders here. The law's CPU term should bind earlier on 2 cores; refit `AGENT_CORE`.

## Cost and limits

- About $40: 48 builders.
- 2 CPUs, one project, two teams per arm.
