# Gate 46 results: a lead with a shared brain over the swarm, on a deep project, Oct 29 2026

**Question** (from the user). Does a two-level swarm do better than a flat silent one: one lead agent that maps the dependency levels, names the shared interfaces and keeps a shared `BRAIN.md` current, over the builders? Tested on a deep project, where everything depends on foundations that are not yet built.

**Answer.**
- **No. The lead and brain made the swarm about 20% slower and 9% costlier, with the same result.** Every team built the whole SQL engine from the 221-line skeleton to 1,340 of 1,340 visible tests, and 99.8% of the hidden suite.

| Team | Time to 95% of tests | Last landing | Cost (lead) | Landings | Hidden |
| --- | --- | --- | --- | --- | --- |
| F1 (7 flat) | **4.4 min** | 4.5 min | $5.51 | 27 | 99.8% |
| H1 (lead + 6) | 6.2 min | 7.9 min | $5.76 ($0.17) | 30 | 99.8% |
| H2 (lead + 6) | 6.7 min | 7.0 min | $6.17 ($0.20) | 29 | 99.8% |
| F2 (7 flat) | **6.3 min** | 6.3 min | $5.41 | 22 | 99.8% |

Means: flat 5.3 minutes, lead 6.4 (1.20×); cost 1.09×. The registered kill fired: not sooner, and costlier.

- **The plans were good.** Each lead pushed its plan in 35 seconds:
  - every category in dependency levels;
  - an interface contract (one values module, a function registry that loads one file per family, an expression format, separate select and DML executors);
  - one owner per file.
  - The workers followed them; there were no duplicate-definition blocks and almost no conflicts.
- **That is exactly why they were slower.** The plan front-loaded a proper foundation, and workers waited for level 0 before building on it:
  - The lead teams first passed 300 tests at 2.6 and 4.3 minutes.
  - The flat teams got there at 1.6 and 2.0 minutes, by hacking the pieces they needed in parallel and merging.
  - On this project the critical path was the foundation, and a plan that serializes work onto it lengthens it. That is Brent's limit at work.
- **Discovered: coupling stays low even on a deep project.** Flat builders starting from a skeleton did not pile up:
  - no duplicate-definition blocks;
  - one brief break of main per team at most (F1 fell from 943 to 444 for one commit and was fixed in seconds);
  - the lead teams had one too (H1, 104 to 27).
  - Silent builders put new features in their own modules unprompted, as in Gate 2.
  - The law's small coupling term held where we expected it to fail.

## Setup

- **Project:** Gate 1's skeleton (lexer, parser, engine stub; 221 lines) with the scale project's 1,340 visible tests in 127 categories. At the start, 9 pass. Protocol v2 (claims, the guard). Hidden: gen2.py, seed 5000000, private; `median`, `percentile` and `transactions` left out (local SQLite disagrees with the stored answers), 2,200 scored.
- **Teams:** 7 agents each, alone on the 2-CPU machine, ABBA: F1, H1, H2, F2. Predictions pushed before any team ran (`648bcca`). The seed was then found broken and fixed before the scored run (`0ae03f4`); see *Lab error* below.
  - **F:** 7 silent workers, Gate 3's prompt.
  - **H:**
    - The lead (Claude; Codex is not installed here) pushes `BRAIN.md` first, then updates it every 2–3 minutes. Each lead pushed its plan and 3 updates.
    - 6 workers start when the plan is on main. They follow it and leave usage notes in `brain/notes/`.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| D1 | Each plan on main within 6 minutes | **Held:** 35 s and 35 s |
| D2 | The lead is not ≥ 20% sooner to 95% | **Held:** 1.20× *slower* |
| D3 | The lead costs ≥ 1.10× | **Failed, just:** 1.09× (the lead itself cost $0.17–0.20; its workers spent a little more) |
| D4 | At 10 minutes the lead teams have fewer tests passing | **Failed, uninformative:** every team was at 1,340 by 10 minutes. The registered 10- and 20-minute points were too late for a build this fast. The first-300 times above show the early gap |
| D5 | Hidden within 3 points | **Held:** 99.8% all four |
| Ship | Lead ≥ 20% sooner in both pairings | **Did not fire** |
| Kill | Not sooner, and costlier | **Fired** |

## What it means

1. **A planner pays only when collisions cost more than the plan's serialization.** Here collisions were rare even from a skeleton, so the plan's cost (waiting for a clean foundation) was not repaid. Hive stays flat. The team notes switch on only when builders actually collide.
2. **The shared brain is worth keeping as a document, not as a boss.** Its interface contract is what a careful senior engineer would write, and the builders used it. A cheap middle path is the first builder writing such a contract as one claimed task, with no one waiting on it. That is untested, and nothing here says it would pay.
3. **Codex as the lead** would test the brand, not the structure. The structure lost by 20% because of the critical path, not because of the lead's quality: the plans were good and quick. A Codex lead is unlikely to change that, but it can be run with these files on the user's machine.

## Lab error (disclosed)

The first seed commit deleted the old engine but never added the skeleton, so the project had no engine. In that aborted launch:
- the flat team stopped within 30 seconds and asked;
- a lead team made "land a skeleton" its first task and built the whole engine from nothing in about 9 minutes.

Nothing from it is scored; see `aborted_run/NOTE.md`. The seed was rebuilt, checked at 9/1,340 from a fresh clone, and the gate rerun from scratch.

## Limits

- One project, 7 agents, Claude as lead and builders. Builds of 4–8 minutes leave little room for any coordination gain; a much larger codebase could differ.
- 2 CPUs. Within-arm spread was 4.4 vs 6.3 minutes for flat and 6.2 vs 6.7 for lead, so a 1.2× difference is real but not large.
- Workers mostly did not export their event logs, so conflict counts are partial; breaks of main are counted from replaying every commit.

## Files

`prompts/` (flat, worker and lead prompts; predictions), `seed_deep.bundle`, `referee/` (driver, analysis), `results/` (analysis, per-team summaries with progress after every commit, worker costs, both leads' plans and final brains, lead outputs, run log), `swarms/` (all four teams' histories), `logs/`, `aborted_run/`.
