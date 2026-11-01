# Gate 75 predictions: time to accuracy on an engineering-heavy job, split swarm against one agent

Registered Nov 1 2026, before any team runs. The user: "accuracy with reduced time will suffice the cost". Synthetic owner only.

## Why this test

- **Gate 74:** the split swarm (6 engine builders and 1 business builder) got the owner's rules as right as one agent, or more (97.8 vs 95.2%). Its speed was not shown, for two reasons:
  1. its measure ("every visible test passes") is met by guesses before the owner has answered;
  2. that job had 22–26 owner decisions, so the owner's answering (60 s each) took as long as the engineering for both arms.

  An exploratory replay of Gate 74 (not registered) found both arms reached their final business accuracy at about the same time.
- **The swarm's speed can only show where the engineering outweighs the decisions,** which is the common case: a feature with a lot of building and a handful of rules.
- **This gate:** such a job, scored by the honest measure. How many minutes until the build is actually accurate, on hidden tests?

## Setup

- **The job:** Gate 46's deep project (a skeleton to 1,340 engine tests) plus only **4 business functions** with 8 declared decisions, from a fresh independent rule-giver per run. Seeds: g75a 75100/75200000; g75b 75300/75400000.
- **The owner:** Gate 74's: 60 s an answer, one at a time, questions queued, a 90-s ask.
- **Arms:** Gate 74's. A1 is one builder. S7B is 6 engine builders plus 1 business builder (the split Hive now ships). Both get the same "ask systematically" instruction.
- **Order:** each arm runs alone. g75a: A1 then S7B. g75b: S7B then A1.
- **Time to accuracy (T_acc):** every landing on main is probed on the business functions' hidden tests. T_acc is the first landing after which ≥ 99% of visible tests and ≥ 90% of business hidden tests pass, or the arm's wall minutes if never.
- Driver `referee/run75.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (means over the two runs)

| # | Prediction | Odds |
| --- | --- | --- |
| V1 | S7B reaches accuracy in ≤ 0.6× A1's time | 55% |
| V2 | S7B's final business hidden ≥ A1's − 3 | 70% |
| V3 | S7B's final engine hidden ≥ A1's − 1 | 85% |

## Decision rules

- **Claim:** V1 and V2 hold. Hive's split swarm reaches the same accuracy much sooner on an engineering-heavy job, which is the trade the user accepts the extra cost for.
- **If V1 fails:** the owner's answers bind even with 8 decisions. Then look at when the business builder lands relative to the engine.

## Limits

- One run per arm per order; a synthetic owner whose answers never drift, with a simulated pace; a 2-CPU machine.
- About $20 and about 2 hours.
