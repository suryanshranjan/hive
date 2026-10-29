# Gate 51 results: team notes at 12 builders, Oct 30 2026

**Question.** Hive's law switched team notes on for 10 or more builders: a one-line message to the team carried in a landing commit. Do they help 12 builders, the size where Gate 50 found the swarm slower than 7?

**Answer.**
- **No. The size trigger is now off.**

| Team | Time to 95% | Landings | Breaks of main | Notes | Hidden | Cost | Mean load on 2 cores (peak) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 (silent) | 6.6 min | 42 | 1 | – | 99.8% | $8.94 | 3.2 (7.8) |
| T1 (notes) | 5.2 min | 42 | 0 | 18 | 99.8% | $9.31 | 2.8 (6.3) |
| T2 (notes) | 10.8 min | 30 | 1 | 16 | 99.8% | $9.32 | 1.2 (2.8) |
| S2 (silent) | 3.9 min | 36 | 0 | – | 99.8% | $8.97 | 1.1 (2.0) |

Means: silent 5.2 min, notes 8.0 min (1.53×, driven by T2); cost 1.04×. Twelve-builder runs on this project now span 3.9 to 10.8 minutes (five runs with Gate 50's 6.6), against 4.2 to 6.3 for seven. Seven remains the better team.

- **The notes were good.** The builders wrote real interface contracts:
  - "select_exec.run_select(conn, st, evaluate, outer=None) runs SELECT; st keys …"
  - "Window calls parse to ('win',..,idx); exec_select must call window.apply_windows(…)"

  The teams that wrote them were no faster, and broke main no less.
- **The machine did not explain the slow runs.** Mean load ranged from 1.1 to 3.2 on 2 cores. The slowest team (T2) ran on the *least* loaded machine (1.2). Run-to-run variation at 12 builders is large and comes from the builders' own paths through the work, not the CPU. This settles the question Gate 50 left open.

## Setup

- **Project:** Gate 46's deep project (skeleton to 1,340 tests). Hidden suite as in Gate 50.
- **Teams:** 12 builders each, alone on the 2-CPU machine, ABBA. Predictions pushed before any team ran (`7a5de3a`).
  - **S:** silent, Gate 50's prompt.
  - **T:** the same, plus `tools/notes.py` at every sync and before resolving a conflict, and `tools/land_note.py` to land with one line for the team. These are Hive's notes-in-commits design.
- The machine's 1-minute load average was sampled every 10 s.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| F1 | Notes do not make 12 builders ≥ 15% faster | **Held:** 1.53× *slower* on average (one notes team faster, one much slower) |
| F2 | Cost within ±10% | **Held:** 1.04× |
| F3 | The machine is saturated (mean load ≥ 2.0) | **Failed:** 1.1 to 3.2; the slowest team had the lowest load |
| F4 | Each notes team posts ≥ 5 notes | **Held:** 18 and 16 |
| Rule | Keep notes at 10+ builders | **Did not fire** |
| Rule | Turn the size trigger off | **Fired** |

## Turned into the product (this commit)

- `hive/law.py`: `NOTES_FROM_BUILDERS = None`. Size alone no longer turns notes on. They switch on when a swarm's collisions reach 0.5 per landing, a threshold still untested, and every rebase conflict still shows the recent notes. `hive land --note` and `hive notes` stay available to any builder.
- Test updated. Five gates now agree that builders talking, in any form, does not speed the swarm: Gates 43, 44, 46, 51, and the lead in 46.

## Limits

- Two teams per arm, and twelve-builder runs vary a great deal (3.9 to 10.8 minutes). The registered rule fired on means that one slow run drives, so the safe reading is "no gain", not "notes slow builders down".
- One project, 2 CPUs.

## Files

`prompts/` (silent and notes prompts, predictions), `tools/` (notes, land with a note), `referee/` (driver, analysis), `results/` (analysis, every team note, per-team progress and load samples, worker costs, run log), `swarms/`, `logs/`.
