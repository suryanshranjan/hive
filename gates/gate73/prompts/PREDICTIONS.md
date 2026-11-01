# Gate 73 predictions: Hive's swarm, fixed, against one agent on a mixed job with a busy owner

Registered Nov 1 2026, before any team runs. The user: "make hive surpass all levels of agents".

## Why this test

Gate 72 on the same kind of job:
- the swarm reached 95% of the tests 2.4–7× sooner and finished in 0.77× one agent's time;
- but it got the business rules 3.4 points less right.

Two causes were seen in its first run:
1. **Five builders asked the owner the same question at once.** Hive now answers a repeated question from his one answer.
2. **The business functions fell to two builders who asked less.** The proposed fix: Hive asks first. As the build starts, a question writer puts a question to the owner for every open decision of every business function. The builders start on the engine, and read the answers before building each business function.

Both fixes together decide whether the swarm can be sooner *and* as right.

## Setup

- **The job:** Gate 72's: Gate 46's deep project (a skeleton to 1,340 engine tests) plus 10 business functions from a fresh independent rule-giver per run (seeds 73100/73200000 and 73300/73400000).
- **The owner:** at 60 s an answer, one question at a time, questions queued, and the ask tool never blocking past 90 s (Gate 72's amended owner on call).
- **Arms**, each alone on the machine with its own owner on call; all builders told to ask first:

| Arm | What it is |
| --- | --- |
| **A1** | One builder (Gate 72's) |
| **S7D** | Hive's 7 builders with the repeated-question rule: a question asking the same decision as an earlier one (one model call, `prompts/same_brief.md`) is not put to the owner; it gets the earlier answer |
| **S7Q** | S7D plus Hive asking first (`prompts/question_writer.md`), queued as the builders start |

- **Order:** g73a: A1, S7D, S7Q. g73b: S7Q, S7D, A1.
- **Questions counted:** those put to the owner. A repeated question answered from an earlier one is not counted.
- Driver `referee/run73.py`, analysis `referee/analyze.py`, owner `referee/owner_server.py`, all committed now.

## Predictions (means over the two runs)

| # | Prediction | Odds |
| --- | --- | --- |
| Y1 | S7Q passes every visible test in ≤ 0.8× A1's time | 50% |
| Y2 | S7Q's business hidden ≥ A1's − 2 | 50% |
| Y3 | S7D's business hidden ≥ A1's − 2 | 40% |
| Y4 | S7D puts ≤ 1.1× A1's questions to the owner | 50% |

## Decision rules

- **Claim:** Y1 and Y2 hold. Hive's swarm, as fixed, beats one agent on a mixed job: sooner and as right. Hive's builds then ask first through Hive (a question writer as the build starts), with the repeated-question rule.
- **If Y2 fails:** the swarm's business shortfall is not the questions' fault. Look at who builds the business functions.

## Limits

- One run per arm per order; a synthetic owner whose answers never drift, with a simulated pace; a 2-CPU machine.
- About $40 and about 4 hours.
