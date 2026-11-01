# Gate 79 predictions: the map where finding the code is the work, put where builders cannot miss it

Registered Nov 1 2026, before any run. The user: "Go on" (after Gate 78).

## Why this test

- **Gate 78:** no builder opened the graphify map (0 of 8). The goal named every function's file, so finding the code took one grep, and the models know sqlglot.
- **Two changes, both from graphify's own design:**
  1. **The job:** finding the code is the work. Builders get users' bug reports (what they ran, what they got, what they expected), never a file or function name. This is the owner's usual case: he says what is wrong, not where.
  2. **The guidance:** graphify's way of putting the map in front of Claude Code:
     - its rule ("query the graph before your first grep or file read"), in each clone's `CLAUDE.local.md`;
     - its PreToolUse hook, which adds a reminder of the map to every search and file read (`.claude/settings.local.json`).

     Both are kept out of git. A check before registering showed that a headless `claude -p` receives the hook's reminder.

## Setup

- **The job:** sqlglot 30.27.0 (MIT; 85,000 lines) with 12 planted bugs, from `referee/pick79.py` (seed 79).
  - Each bug is one small change in one function: a comparison flipped, `and`/`or` swapped, a `not` dropped, or an integer + 1.
  - Each qualified if the package still imports and 1–12 fast-suite test methods fail.
  - At most 2 per file; 11 files in all.
- **The builders' goal:** 11 bug reports (two bugs show as one report), written by `referee/seed79.py`. Each report's output and expected output are computed by running it on the seed and on the original.
- **The hidden suite:** the 25 fast-suite test methods (of 1,179) that fail with the bugs. They are removed from the seed, run from sqlglot's own test files, and kept in `private/g79` until scored.
- **Areas:** one per report (`bug01` … `bug11`), so builders do not duplicate work (Gate 78's observation).
- **Arms**, each 4 builders through the product, with no owner and 30 minutes:
  - **H:** as shipped;
  - **HG:** the map (`hive/codemap.py`, about a minute to build) in every clone, with graphify's rule and hook (`map_guide`), and graphify on the builders' PATH.
- **Order:** H1, HG1, HG2, H2, H3, HG3, each alone.
- Driver `referee/run79.py`, analysis `referee/analyze.py`, committed now. The goal text is in `private/g79/goal.md` until scored.

## Measures

- **Hidden:** passed of 25, at the end and at every landing.
- **Time to accuracy:** minutes from the start of preparing the swarm, so the map's build counts, to the first landing with ≥ 23 of 25.
- **Builders' cost,** and tool calls per builder from their transcripts.

## Predictions (means over 3 runs per arm)

| # | Prediction | Odds |
| --- | --- | --- |
| G1 | In each HG run, ≥ 3 of 4 builders run graphify | 70% |
| G2 | HG cost ≤ 0.85× H | 35% |
| G3 | HG time to accuracy ≤ 0.85× H | 30% |
| G4 | HG hidden ≥ H − 2 (of 25) | 75% |
| G5 | HG reads and searches per builder ≤ 0.8× H | 40% |

## Decision rules

- **Claim (G1 and (G2 or G3) and G4):** the guided map ships, on when graphify is installed.
- **G1 holds, G2 and G3 fail:** builders use the map, but it does not pay. It stays off.
- **G1 fails:** even guided, builders do not use it. It stays off, and graphify is not worth recommending to Hive's builders.

## Limits

- Three runs per arm, on one codebase the models partly know, on a 2-CPU machine.
- The bugs are small planted mutations, not real ones.
- About $20–40 and about 2–3 hours.
