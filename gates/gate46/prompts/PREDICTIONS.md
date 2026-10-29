# Gate 46 predictions: a lead with a shared brain over the swarm, on a deep project

Registered Oct 29 2026, before any team runs. Asked for by the user: one agent coordinating a swarm, with multi-level dependencies and a bigger shared brain. The user named Codex as the lead. Codex is not installed or logged in on this machine (it runs only in the user's container, with his login), so the lead here is Claude. This tests the structure, not the brand; a Codex lead can be rerun later on the user's machine with the same files.

## Why this test

Hive's builders are flat and silent: claims and the guard coordinate them. Two results support that so far: talking added nothing (Gates 43, 44), and "foundation first" did not pay (Gate 1). But every project since Gate 1 started with the foundations already built, so dependencies were shallow. The law's coupling term (κd ≈ 0.013) comes from such work.

On a deep project the picture could change. From a skeleton, almost every category needs the same foundations: expression evaluation, types, the SELECT core. Flat builders might all start rebuilding those at once and collide. A lead who maps the dependency levels, names the shared interfaces, and keeps a shared brain current is the obvious fix. The law says what it can and cannot win:
- It cannot shorten the critical path (Brent's limit).
- It can cut collisions and duplicated foundations.
- It costs an extra agent and a serial planning delay before anyone builds.

What we want to discover: how high the coupling gets on a deep project, and whether a plan pays for itself there.

## Setup

- **Project:** Gate 1's 221-line skeleton engine (lexer, parser, engine stub) with the scale project's 1,340 visible tests in 127 categories. At the start, 9 pass (`seed_deep.bundle`). Protocol v2 tools (claims, the guard). Hidden suite: gen2.py, seed 5000000, generated privately, never committed; categories where this SQLite disagrees with the stored visible answers are left out (Gate 43's rule).
- **Teams:** 7 agents each, run one after another, each alone on the 2-CPU machine, in ABBA order: F1, H1, H2, F2.
  - **F (flat):** 7 silent workers, Gate 3's prompt (`prompt_flat.md`).
  - **H (lead and brain):**
    - The lead starts first and pushes `BRAIN.md`: every category in dependency levels, the shared interfaces, and what to start with. The lead writes no engine code (`prompt_lead.md`).
    - When the plan is on main, 6 workers start (`prompt_worker_h.md`). They read the brain at every sync, work from the lowest unblocked level, build on the named interfaces, and leave usage notes in `brain/notes/<name>.md`.
    - The lead updates the brain every 2–3 minutes until the work stops.
- **Measured** (times from the team's start; for H, from the lead's start):
  - time to 95% of visible tests;
  - tests passing at 10 and 20 minutes;
  - last landing;
  - cost (workers plus lead);
  - brain updates;
  - hidden pass at the end;
  - conflicts and guard blocks, where workers log them.
- **Driver and analysis:** `referee/run46.py`, `referee/analyze.py`, committed now.

## Predictions (F and H are each the mean of their two teams)

| # | Prediction | Odds |
| --- | --- | --- |
| D1 | Each lead's plan is on main within 6 minutes | 60% |
| D2 | The lead and brain are **not** ≥ 20% sooner to 95% visible (planning delay and the critical path eat most of the gain) | 75% |
| D3 | H costs ≥ 1.10× F | 55% |
| D4 | At 10 minutes H has fewer tests passing than F (its workers start later) | 60% |
| D5 | Final hidden pass within 3 points | 70% |

## Decision rules

- **Ship a lead-and-brain mode** in Hive, for deep projects only (the law decides when): H reaches 95% ≥ 20% sooner in both pairings, at ≤ 1.15× the cost.
- **Kill:** H is not sooner and costs more. Flat stays, and the result goes in the law as the measured coupling of a deep project.

## Cost and limits

- About $30 to $50: 28 agents on a much larger build than Gates 43–44.
- 2 CPUs; one project; one lead model.
- A team may not reach 95% within its 45 minutes. Then the comparison uses tests passing at 10 and 20 minutes and at the end, reported as such.
