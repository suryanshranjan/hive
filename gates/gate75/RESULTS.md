# Gate 75 results: time to accuracy on an engineering-heavy job, split swarm against one agent, Nov 1 2026

**Question** (the user: "accuracy with reduced time will suffice the cost"). On a job with much more engineering than owner decisions, does Hive's split swarm reach the same accuracy sooner than one agent? Time is measured by the honest clock: minutes until the build actually passes hidden tests.

**Answer.**
- **Yes: the claim fired.** The split swarm got as right as one agent, or more, in **less than half the time** (0.45×).

| Means over 2 runs | Time to accuracy | Final business hidden | Final engine hidden | Questions | Cost |
| --- | --- | --- | --- | --- | --- |
| One agent (A1) | 27.1 min | 86.5% | 99.8% | 10.5 | $2.95 |
| **Hive's split swarm (S7B)** | **12.1 min** | **90.0%** | 99.8% | 11.0 | $5.75 |

- **Run g75a:** both ended at the same accuracy (business 82.0%, engine 99.8%). Neither passed 90% of the business hidden tests, so both are timed by when they finished: 10.1 min for the swarm, 31.1 for one agent (0.32×).
- **Run g75b:** the swarm passed 98.0% of business hidden tests at 14.1 min; one agent reached 91.0% at 23.2 min (0.61×).
- **Why the swarm wins here:**
  - With 8 owner decisions, his answers take about 10 minutes.
  - The business builder asks them while six builders build the engine, and lands as soon as the engine's core is in (at about 5–10 minutes).
  - One agent must do both in series: 23–31 minutes.
  - On Gate 74's job (22–26 decisions), his answers took as long as the engineering, and neither arm was sooner.
- **Cost:** about 1.95× ($5.75 vs $2.95). This is the trade the user accepts: the same accuracy, sooner.

## Setup

- **The job:** Gate 46's deep project (a skeleton to 1,340 engine tests) plus 4 business functions with 8 declared decisions, from a fresh independent rule-giver per run (published after scoring in `referee/oracle_g75*.py`).
- **The owner:** at 60 s an answer, one at a time, queued, a 90-s ask.
- **Arms:** Gate 74's. A1 is one builder. S7B is 6 engine builders and 1 business builder, the split Hive ships since Gate 74. Both get the same "ask systematically" instruction.
- **Order:** each arm ran alone on the machine. g75a: A1 then S7B. g75b: S7B then A1.
- **Time to accuracy:** every landing on main was probed on the business functions' hidden tests. The time is the first landing after which ≥ 99% of visible tests and ≥ 90% of business hidden tests pass, or the arm's wall minutes if never.
- Predictions pushed before any team ran (`8211f6e`). Builders cost $17.4 in all.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| V1 | S7B reaches accuracy in ≤ 0.6× A1's time | **Held:** 0.45× |
| V2 | S7B final business ≥ A1 − 3 | **Held:** +3.5 |
| V3 | S7B final engine ≥ A1 − 1 | **Held:** 0.0 |
| Claim | V1 and V2 | **Fired** |

## What it means

1. **Hive's split swarm beats one agent where most real features sit:** a lot of building and a handful of owner decisions. Same or better accuracy, in less than half the time, at about twice the cost.
2. **Where the owner's decisions dominate** (Gates 71, 74), his answering is the clock for both and the swarm is no sooner. Its accuracy now matches or beats one agent's (Gate 74).
3. **No new product change.** This confirms the split shipped after Gate 74.

## Limits

- One run per arm per order; a synthetic owner whose answers never drift, with a simulated pace; a 2-CPU machine.
- In run g75a the time was set by when each team stopped, as neither reached 90% on the business tests.

## Files

`prompts/` (4-function rule-giver; engine, business and single-agent prompts; predictions).

`referee/`:
- `run75.py`, `analyze.py` (time to accuracy), `owner_server.py`, `ask_owner.py`;
- the published rule sets.

`results/g75a/`, `results/g75b/`:
- every question and answer;
- probes, team progress, agents and run logs.
