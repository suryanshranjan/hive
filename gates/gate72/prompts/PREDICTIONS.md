# Gate 72 predictions: a mixed job (an engine plus business functions), one agent against Hive's swarm, with a busy owner

Registered Nov 1 2026, before any team runs. The user: "I think a swarm of agents can beat an agent, simple as that." Synthetic owner only.

## Why this test

- **Gate 71 (running):** on a job that is all business decisions, the owner answering at a person's pace sets the pace for both one agent and the swarm, and the swarm asks more.
- **Gate 50:** on pure engineering, 7 builders were 3× faster than one.
- **Real features mix the two:** a lot of engineering, plus the decisions only the owner can make. Hive's claim to beat one agent rests on such jobs: the swarm builds the engineering in parallel while the owner answers.

## Setup

- **The job:** Gate 46's deep project (a 221-line skeleton to 1,340 engine tests) plus 10 business functions from a fresh independent rule-giver (25 declared decisions; 2 examples each). The business functions need the engine to run at all.
  - Run g72a: seeds 72100, 72200000. Run g72b: seeds 72300, 72400000.
- **The owner:** on call at a person's pace. Every answer takes at least 60 s, and he answers one question at a time (Gate 71's server).
- **Arms**, both told to ask him about every open decision of a business function before building it:
  - **A1:** one builder.
  - **S7:** 7 builders who read the team's answers first.
- **Order:** each arm runs alone on the machine; g72a: A1 then S7; g72b: S7 then A1. Builders stop at 90 minutes.
- **Measures:**
  - minutes to 95% and to all visible tests;
  - the engine's hidden suite (Gate 50's);
  - the business functions' hidden tests;
  - questions;
  - cost.
- Driver `referee/run72.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (means over the two runs)

| # | Prediction | Odds |
| --- | --- | --- |
| X1 | S7 passes every visible test in ≤ 0.7× A1's time | 55% |
| X2 | S7's business hidden ≥ A1's − 3 | 65% |
| X3 | S7's engine hidden ≥ A1's − 1 | 80% |
| X4 | S7 asks ≤ 1.5× A1's questions | 45% |

## Decision rules

- **Claim:** X1, X2 and X3 hold. On a job that mixes engineering with the owner's decisions, Hive's swarm beats one agent: sooner, and as right.
- **If X1 fails:** the owner's pace binds even here. Hive's speed claim is then limited to jobs whose decisions are few next to their engineering.

## Limits

- One run per arm per order, on a 2-CPU machine. Gate 46's identical teams differed by about 30% in time.
- A synthetic owner whose answers never drift; his pace is simulated.
- About $30 and about 3 hours.

## Amendment, Nov 1 2026, before any team ran

Gate 71's first run found that a swarm loses answers when a slow owner is shared. A builder's command is cut off at 2 minutes, and with 7 builders queued on one owner answering every 60 s, questions waited longer than that. Builders guessed, and the answers arrived too late (S7 85.0% vs A1 97.6%). Before any Gate 72 team ran, the owner on call was changed:
- questions queue at once;
- the ask tool waits at most 90 s, then says the question is with him;
- builders are told to work on another part meanwhile, and to read the answers before building the part it decides.

The same applies to both arms (A1 never waits long). Hive's `hive ask` gets the same change. The predictions and the analysis are unchanged.
