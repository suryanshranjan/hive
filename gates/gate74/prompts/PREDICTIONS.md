# Gate 74 predictions: a split swarm (6 engine builders and 1 business builder) against one agent on a mixed job

Registered Nov 1 2026, before any team runs. The user: "make hive surpass all levels of agents". Synthetic owner only.

## Why this test

In Gates 72 and 73 the swarm built the engine 2.4–7× sooner than one agent, but got the business rules less right (Gate 72: 93.8 vs 97.2%; Gate 73's first run: 86.8–88.8 vs 99.6%), even when Hive asked every question first.

Reading the questions explains it. The single agent covers each business function systematically: the rule, then rounding, then missing or invalid input. The swarm's questions were scattered, and its business functions were built in bulk by one or two builders racing to finish.

Hypothesis: split the work by kind. Six builders build the engine and never touch the business functions. One **business builder** owns all ten and asks the owner systematically, as the single agent does. The swarm should then keep its engineering speed while matching the agent's care.

## Setup

- **The job:** Gate 72's mixed job (Gate 46's skeleton to 1,340 engine tests, plus 10 business functions from a fresh independent rule-giver per run; seeds 74100/74200000 and 74300/74400000).
- **The owner:** Gate 72's owner on call: 60 s an answer, one at a time, questions queued, the ask tool never blocking past 90 s.
- **Arms**, each alone on the machine with its own owner on call. Both get the same ask instruction, including "ask systematically: the rule, rounding and form, boundaries, blank/missing/negative/odd input":
  - **A1:** one builder;
  - **S7B:** 6 engine builders (`prompts/prompt_engine.md`; they never claim a business function) and 1 business builder (`prompts/prompt_business.md`; it owns the 10 functions and starts asking at once, while the engine is built).
- **Order:** g74a: A1 then S7B. g74b: S7B then A1.
- **Finish:** the first landing after which every visible test passes, or the arm's wall minutes if that never happens.
- Driver `referee/run74.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (means over the two runs)

| # | Prediction | Odds |
| --- | --- | --- |
| Z1 | S7B finishes in ≤ 0.8× A1's time | 55% |
| Z2 | S7B's business hidden ≥ A1's − 2 | 55% |
| Z3 | S7B's engine hidden ≥ A1's − 1 | 80% |
| Z4 | S7B's business builder asks ≥ 0.8× A1's questions | 60% |

## Decision rules

- **Claim:** Z1 and Z2 hold. Hive's split swarm beats one agent on a mixed job: sooner and as right. Hive then gives the owner's decisions to one dedicated builder per build, and the engineering to the rest.
- **If Z2 fails with Z4 held:** asking alone does not carry the care. Look at how the business builder builds.

## Limits

- One run per arm per order; a synthetic owner whose answers never drift, with a simulated pace; a 2-CPU machine.
- About $25 and about 2.5 hours.
