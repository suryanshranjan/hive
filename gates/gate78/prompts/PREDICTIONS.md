# Gate 78 predictions: a map of the codebase for the swarm (graphify)

Registered Nov 1 2026, before any run. The user: "use graphify … use good qualities of it, will help in both scopes".

## Why this test

- **graphify** (`pip install graphifyy`, Apache-2.0, graphify.com) turns a codebase into a knowledge graph.
  - It reads the code's syntax on this computer, with no model and no cost.
  - It groups related code into communities, finds the most connected functions, and tags each edge as read from the code (EXTRACTED) or guessed (INFERRED).
  - It answers `query`, `explain`, `path` and `affected` from the graph instead of reading files.
  - Its claim: fewer tokens per question about a codebase. Its own benchmark compares the map with reading every file, which no agent does, so the claim is untested for builders.
- **Hive's builders find their way alone.** Each reads the same files to learn the codebase (Gates 1–3: onboarding about 110k tokens per builder), and every gate so far used small or skeleton projects.
- **This gate:** on a large real codebase, does one shared map, built once before launch, make the swarm cheaper or faster without making it less right?

## Setup

- **The job:** sqlglot 30.27.0 (MIT, from PyPI; a SQL parser, transpiler and optimizer, 85,000 lines; not installed on this machine).
  - 12 module-level functions in 10 files were emptied: each only raises NotImplementedError. They were chosen at random (seed 78) by `referee/pick78.py`: 8–40 lines each, each breaking 1–12 test methods alone, at most 2 per file.
  - Every fast-suite test method that then failed (61 of 1,179) was removed from the visible repo (`referee/seed78.py`).
  - **The hidden suite** is those 61 methods, run from sqlglot's own test files against the final code. It is regenerated from the seed and the public release, and kept in `private/g78` until scored.
- **The goal** lists the 12 functions. It says to rebuild each from the code around it, to add tests, and never to install, download or look at another copy of sqlglot.
- **Arms**, each 4 builders through the product (`hive.swarm.prepare` + `launch`), with no owner and 30 minutes:
  - **H:** Hive as shipped;
  - **HM:** the same, plus one map built before launch (`hive/codemap.py`: graphify's code-only extraction, its groups named by one Haiku call, about a minute in all), copied into every clone, kept out of git. The prompt tells builders to ask it (`query`, `explain`, `path`, `affected`) instead of reading file after file, and that `graphify update .` refreshes it.
- **Order:** H1, HM1, HM2, H2, each alone on the machine.
- Driver `referee/run78.py`, analysis `referee/analyze.py`, both committed now.

## Measures (per run, then means over 2 runs per arm)

- **Hidden:** passed of 61 at the end, and at every landing on main.
- **Time to accuracy:** minutes from launch to the first landing with ≥ 55 of 61 hidden, or the wall minutes to the last builder's stop if never.
- **Builders' cost** ($, from the agents' own accounts), and tokens.
- **Finding their way:** Read, Grep, Glob and searching shell commands per builder, and graphify commands, from the builders' transcripts.
- **Leak check:** any command reaching another copy of sqlglot.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| M1 | In each HM run, ≥ 3 of 4 builders use graphify at least once | 75% |
| M2 | HM's builders' cost ≤ 0.85× H's | 35% |
| M3 | HM's time to accuracy ≤ 0.85× H's | 35% |
| M4 | HM's final hidden ≥ H's − 3 (of 61) | 80% |
| M5 | HM's reads and searches per builder ≤ 0.8× H's | 45% |

## Decision rules

- **Claim (M2 or M3, and M4):** the map ships, on by default when graphify is installed. Hive builds it before launch, and `hive doctor` suggests installing graphify.
- **If M1 fails:** builders ignore the map. Then the question becomes how to put it in front of them (graphify's own Claude Code hook), not whether it helps.
- **If M1 holds but M2 and M3 fail:** a map does not pay on this job. It stays off; note that sqlglot is well known to the models, which favours no map.

## Limits

- Two runs per arm, on one codebase that the models may partly know, on a 2-CPU machine.
- The hidden suite tests the 12 functions only through sqlglot's own tests.
- About $30–50 and about 2.5 hours.
