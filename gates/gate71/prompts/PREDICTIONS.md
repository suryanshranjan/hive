# Gate 71 predictions: a big job with a busy owner, one agent against Hive's swarm

Registered Nov 1 2026, before the run. It follows Gate 68 under the user's "hive needs to surpass everything". Synthetic owner only.

## Why this test

- **Gate 68:** with builders who ask first, Hive's swarm and one agent got the same result on a 10-function job. So Hive's edge, if any, is elsewhere.
- **Gate 50:** on big engineering work, 7 builders were 3× faster than one.
- **The open question:** on a big job full of business decisions, every builder waits on the same owner, who answers at a person's pace. Does the swarm's speed survive, or does the owner become the bottleneck for both?

## Setup

- **The job:** 20 business functions (19 scalars and 1 aggregate) with 50 declared decisions, from a fresh independent rule-giver per run: g71a (seeds 71100, 71200000) and g71b (seeds 71300, 71400000).
- **The owner:** Gate 68's owner on call (answers from his policy; lists answers so far), slowed to a person's pace. Each answer takes at least 60 s, about Gate 27's founder's median, and he answers one question at a time.
- **Arms**, both told to ask first:
  - **A1:** one builder.
  - **S7:** 7 builders who read the team's answers before asking.

  Each arm has its own owner on call, and the arms run one after the other, alone on the machine (g71a: A1 then S7; g71b: S7 then A1). Builders stop at 90 minutes.
- **Measures:**
  - minutes from the arm's first builder start to its last builder end;
  - hidden pass;
  - questions asked;
  - the owner's busy share (questions × 60 s ÷ minutes).
- Driver `referee/review71.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (means over the two runs)

| # | Prediction | Odds |
| --- | --- | --- |
| T1 | S7 takes ≤ 0.67× A1's minutes | 45% |
| T2 | S7 hidden ≥ A1 − 3 | 70% |
| T3 | S7 asks ≤ 1.5× A1's questions | 50% |
| T4 | The owner is S7's bottleneck (busy share ≥ 0.6) | 50% |

## Decision rules

- **Claim:** T1 and T2 hold. Hive's swarm keeps its speed on a big job with a busy owner.
- **If T1 fails and T4 holds:** the owner is the bottleneck. The next lever is asking him in batches before building (the builders' own questions, collected first), so his answers are not serialized across builders.

## Limits

- A synthetic owner whose answers never drift; his pace is simulated. One run per arm per rule set, on a 2-CPU machine.
- About $25 and about 3 hours.
