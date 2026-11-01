# Gate 71 results: a big job with a busy owner, one agent against Hive's swarm, Nov 1 2026

**Question** (the user: "I think a swarm of agents can beat an agent"). On a 20-function job full of business decisions, with the owner answering at a person's pace (60 s an answer), does Hive's swarm of 7 asking builders beat one asking agent?

**Answer.**
- **No. The owner set the pace for both, and the swarm lost answers.** The claim did not fire.

| Means over 2 fresh rule sets | Minutes | Hidden pass | Questions | Owner busy share | Cost |
| --- | --- | --- | --- | --- | --- |
| One agent (A1) | 48.1 | **94.1%** | 45.0 | 0.92 | $0.85 |
| Hive's 7 builders (S7) | 47.9 | 85.4% | 49.5 | 1.03 | $1.98 |

- **Both were owner-bound.** Each arm kept the owner busy almost all of its time (busy share 0.92 and 1.03), so the swarm's parallel building bought nothing: the same 48 minutes.
  - The single agent's time followed its questions: 25 questions in 27.7 min (g71a), 65 in 68.6 min (g71b).
- **The swarm was less right, because it lost answers.**
  - **The mechanism:** a builder's command is cut off at 2 minutes. With 7 builders queued on one owner answering every 60 s, many questions waited longer than that. The builder moved on with a guess, and the answer came too late.
  - **Evidence:** the builders' own reports in 7 of the 14 swarm sessions mention timed-out questions ("timed out at 2 minutes (the answer arrived later)").
  - The single agent's questions waited only for their own answer.
- **Shipped from this failure:**
  - `hive ask` now waits at most 90 s, then says the question stays with the owner;
  - the builder works on another part, and reads `hive answers` before building the part it decides.

  Gate 72 runs with that fix.

## Setup

- **Rules:** two fresh rule sets of 20 functions (19 scalars and 1 aggregate) with 50 declared decisions each, published after scoring in `referee/oracle_g71*.py`.
- **The owner:** Gate 68's owner on call, held to at least 60 s an answer, one question at a time.
- **Arms:** both told to ask first; S7's builders read the team's answers first.
- **Order:** each arm ran alone on the machine. g71a: A1 then S7. g71b: S7 then A1.
- Predictions pushed before the run (`060b7f6`).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| T1 | S7 ≤ 0.67× A1's minutes | **Failed:** 1.00× |
| T2 | S7 hidden ≥ A1 − 3 | **Failed:** −8.7 |
| T3 | S7 asks ≤ 1.5× A1 | **Held:** 1.10× |
| T4 | The owner is S7's bottleneck (busy ≥ 0.6) | **Held:** 1.03 |
| Claim | | **Did not fire** |
| Registered next step (T1 failed, T4 held) | Ask in batches so answers are not serialized across builders | Partly taken up: Gate 72 queues questions and never blocks a builder past 90 s |

## Disclosed

- **The first g71b attempt died midway.** The container restarted at 04:10, while the swarm's builders were working. Its log is kept (`results/g71b_first_attempt_died.log`). g71b was rerun from scratch with a fresh rule set and the same harness as g71a.
- The 2-minute cutoff belongs to the builders' own tool, not to the lab's owner (its socket waited 10 minutes). It is a real limit of the product's builders too.

## What it means

1. **On a job whose work is mostly the owner's decisions, the owner's pace is the job's pace.** No team size changes that: one asking agent took the time of its questions, and so did the swarm.
2. **A swarm must never let a question block a builder.** Shipped in `hive ask`.
3. **Where a swarm can still win** is where there is more engineering than decisions, so it can build while the owner answers. Gate 72 tests that.

## Files

`prompts/` (20-function rule-giver, builder prompt, predictions).

`referee/`:
- `review71.py`, `owner_server.py` (with `--min-seconds`), `ask_owner.py`, `analyze.py`;
- the published rule sets.

`results/g71a/`, `results/g71b/`:
- every question and answer;
- probes, summaries, agents and run logs.
