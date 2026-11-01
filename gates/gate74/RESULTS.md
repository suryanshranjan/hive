# Gate 74 results: a split swarm (6 engine builders and 1 business builder) against one agent, Nov 1 2026

**Question** (the user: "get the best quality of the agent in swarms"). Gates 72–73 found the swarm builds the engine far sooner than one agent, but gets the owner's business rules 3–7 points less right. If one builder owns every business function and asks the owner systematically, as the single agent does, while six build the engine, is the swarm then as right, and sooner?

**Answer.**
- **As right, and more: yes. Sooner to the finish: not by the registered measure.** The claim did not fire, because Z1 failed.

| Means over 2 runs | Business hidden | Engine hidden | 95% visible | All visible | Wall | Questions | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| One agent (A1) | 95.2% | 99.8% | 24.5 min | **25.8 min** | 34.0 min | 23.0 | $2.84 |
| **Split swarm (S7B)** | **97.8%** | 99.8% | **4.9 min** | 27.1 min | **27.4 min** | 24.0 | $6.59 |

- **The swarm's quality gap closed.**
  - The unsplit swarms trailed one agent by 3.4 (Gate 72), 7.2 (Gate 73, repeated-question rule) and 6.0 points (Gate 73, Hive asking first).
  - The split swarm led by 2.6: 95.6 vs 95.6% in g74a, 100.0 vs 94.8% in g74b.
  - Its business builder asked about as many questions as the single agent (22 and 26 vs 23 and 23), and only it asked. The six engine builders asked nothing.
- **The engineering stayed fast.** The split swarm reached 95% of visible tests in 4.9 minutes in both runs, against 36.7 and 12.3 for one agent.
- **To "all visible tests", the agent was about as fast.**
  - "All visible" counts each business function's two examples, which a guess can pass before the owner has answered.
  - In g74b the agent passed every visible test at 14.0 minutes, then kept asking the owner until 23.5 minutes and stopped at 26.7.
  - By wall time to the last builder's stop, the split swarm took 0.81× the agent's time (27.4 vs 34.0 min). That was not the registered measure, so the speed claim is not made.
- **The swarm costs 2.3× as much** ($6.59 vs $2.84).

## Setup

- **The job:** Gate 72's mixed job (Gate 46's skeleton to 1,340 engine tests, plus 10 business functions from a fresh independent rule-giver per run; the rule sets are published after scoring in `referee/oracle_g74*.py`).
- **The owner:** at 60 s an answer, one at a time, questions queued, a 90-s ask.
- **Both arms** were given the same ask instruction, including "ask systematically: the rule, rounding and form, boundaries, blank/missing/negative/odd input".
- **S7B:** 6 engine builders who never claim a business function (`prompts/prompt_engine.md`), and 1 business builder who owns all 10 and starts asking at once (`prompts/prompt_business.md`).
- **Order:** each arm ran alone on the machine. g74a: A1 then S7B. g74b: S7B then A1.
- Predictions pushed before any team ran (`8458850`).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| Z1 | S7B finishes (all visible) in ≤ 0.8× A1's time | **Failed:** 1.05× (by wall time 0.81×, not registered) |
| Z2 | S7B business ≥ A1 − 2 | **Held:** +2.6 |
| Z3 | S7B engine ≥ A1 − 1 | **Held:** 0.0 |
| Z4 | S7B's business builder asks ≥ 0.8× A1's questions | **Held:** 1.04× |
| Claim | Z1 and Z2 | **Did not fire** |

## What changes in Hive

**The split ships** (`hive/swarm.py`, `split_roles`). It fixes the swarm's measured quality defect:
- **When:** the owner is there to answer and there are 3 or more builders.
- **The last builder** is the business builder. It alone owns the parts that turn on his business decisions, asks him systematically (the rule, rounding and form, boundaries, bad input), and encodes each answer as a test.
- **The others** build everything else, the machinery first. They do not ask him, and they leave placeholders where one of his decisions is needed.

The speed claim is not made: by the registered measure the split swarm finished no sooner than one agent.

## Limits

- One run per arm per order; a synthetic owner whose answers never drift, with a simulated pace; a 2-CPU machine.
- In a real codebase, which parts "turn on the owner's decisions" is a judgement the builders make. In this job they were labelled as business functions.

## Files

`prompts/` (engine and business builder prompts, the single agent's prompt, owner and rule-giver briefs, predictions).

`referee/`:
- `run74.py`, `owner_server.py`, `ask_owner.py`, `analyze.py`;
- the published rule sets.

`results/g74a/`, `results/g74b/`:
- every question and answer;
- the engine and business builders' rendered prompts;
- probes, team progress, agents and run logs.
