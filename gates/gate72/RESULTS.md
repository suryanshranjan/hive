# Gate 72 results: a mixed job with a busy owner, one agent against Hive's swarm, Nov 1 2026

**Question** (the user: "I think a swarm of agents can beat an agent, simple as that"). On a job that mixes heavy engineering (a SQL engine from a 221-line skeleton) with 10 business functions only the owner can specify, and the owner answering at a person's pace, does Hive's swarm beat one agent?

**Answer.**
- **Partly. The swarm was faster and as right on the engineering, but not decisively faster to the end, and a little less right on the business rules.** The registered claim did not fire: X1 and X2 missed their thresholds narrowly.

| Means over 2 runs | All visible tests | 95% of visible | Engine hidden | Business hidden | Questions | Cost |
| --- | --- | --- | --- | --- | --- | --- |
| One agent (A1) | 29.7 min | 29.3 min | 99.8% | 97.2% | 19.5 | $1.99 |
| Hive's 7 builders (S7) | **22.8 min** | **9.0 min** | 99.7% | 93.8% | 19.5 | $5.73 |

- **The engineering is where the swarm wins.** It reached 95% of the 1,360 visible tests in 5.2 and 12.8 minutes, against 36.6 and 21.9 for one agent: 2.4× to 7× sooner.
- **The owner's questions set the end.** Each arm finished when its business functions were settled.
  - **g72a:** one agent asked 27 questions and finished in 37.2 min; the swarm asked 19 and finished in 23.8.
  - **g72b:** one agent asked 12 and finished in 22.1; the swarm asked 20 and finished in 21.8.
- **The swarm's business shortfall is one run's.**
  - **g72b:** 94.4% each, both missing the same decisions on one function.
  - **g72a:** 93.2% vs 100%. Five of seven builders opened by asking the owner the same question at once. The business functions were then left to two builders, who asked 1–2 questions per function where the single agent asked 2–3.

  Hive now answers a repeated question from the owner's one answer (shipped this morning, after this run); that fix is not yet measured.
- **The swarm costs about 2.9× as much** ($5.73 vs $1.99).

## Setup

- **The job:** Gate 46's deep project (1,340 engine tests from a 221-line skeleton) plus 10 business functions from a fresh independent rule-giver per run (25 decisions; 2 examples each; the rule sets are published after scoring in `referee/oracle_g72*.py`).
- **The owner:** Gate 71's owner on call at 60 s an answer. Amended before any team ran:
  - questions queue at once;
  - the ask tool never blocks past 90 s, and builders work on another part meanwhile.
- **Arms:** both told to ask first.
- **Order:** each arm ran alone on the machine. g72a: A1 then S7. g72b: S7 then A1.
- Predictions pushed before any team ran (`9588f71`, amended `4e819fb`).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| X1 | S7 finishes in ≤ 0.7× A1's time | **Failed:** 0.77× |
| X2 | S7 business hidden ≥ A1 − 3 | **Failed:** −3.4 |
| X3 | S7 engine hidden ≥ A1 − 1 | **Held:** −0.1 |
| X4 | S7 asks ≤ 1.5× A1 | **Held:** 1.00× |
| Claim | | **Did not fire** |

## What it means

1. **"A swarm beats one agent" holds for the engineering, not for the owner's decisions.**
   - Engineering: about 3× sooner on the deep project (Gate 50), 2.4–7× to 95% here, as correct.
   - Decisions: the owner's answers are the job's pace (Gates 71, 72), and no team size changes that.
   - On a mixed job the swarm finishes sooner by the engineering it overlaps with his answering (here 23% sooner on average), at about 3× the cost.
2. **To win outright on mixed jobs, the swarm must ask as thoroughly as one agent, without asking more.** Two levers are shipped:
   - one answer for a repeated question;
   - an ask that never blocks a builder.

   A gate measuring them together is next.
3. **If the owner's time is what matters,** the quickest path is fewer questions per decision, not more builders.

## Limits

- One run per arm per order; a synthetic owner whose answers never drift; his pace is simulated; a 2-CPU machine.

## Files

`prompts/` (mixed-job builder prompt, rule-giver, owner brief, predictions with the amendment).

`referee/`:
- `run72.py`, `owner_server.py` (queued, paced), `ask_owner.py` (90 s), `analyze.py`;
- the published rule sets.

`results/g72a/`, `results/g72b/`:
- every question and answer;
- probes, team progress (`teams_summary.json`), agents and run logs.
