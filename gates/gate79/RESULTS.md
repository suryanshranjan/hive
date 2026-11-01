# Gate 79 results: the map where finding the code is the work, guided as graphify guides Claude Code, Nov 1 2026

**Question** (the user: "Go on", after Gate 78). Gate 78's builders ignored the map because the goal named every file. If they get only users' bug reports, and graphify's own rule and hook steer them to the map, do they use it, and does it pay?

**Answer.**
- **No. Guided, builders glanced at the map and kept grepping.** The claim did not fire.
  - 6 of 12 builders ran graphify, each once, always in the same command as a `grep` (G1 failed: 3, 2 and 1 per run).
  - The builders' reads and searches were not fewer (20.5 vs 18.5 per builder), and the swarm cost 7% more.
- **By the registered clock it was not sooner either:** 0.88× H's time to accuracy (needed ≤ 0.85×), because building the map took 45–70 seconds before launch.

| Means over 3 runs | Hidden (of 25) | Time to ≥ 23, map build included | Launch to last stop | Builders' cost | Reads and searches per builder | graphify calls |
| --- | --- | --- | --- | --- | --- | --- |
| H (as shipped) | 24.0 (25, 22, 25) | 4.0 min | 4.4 min | $1.42 | 18.5 | – |
| HG (map, rule and hook) | 24.7 (25, 24, 25) | 3.5 min | 3.1 min | $1.52 | 20.5 | 6 in all |

- **Why:**
  - On 85,000 lines, `grep -rn` finds a function from a symptom ("POWER(11, 4)", "INFORMATION_SCHEMA") in a second.
  - The map's answers are keyword walks over a 7,400-node graph; builders read the top 20–30 lines and went to grep anyway.
  - The hook's reminder came with every search, and builders did not change course.
- **Unregistered, and not attributable to the map:** from launch, HG's builders stopped sooner (3.1 vs 4.4 min, 0.70×), though they ran graphify only 6 times and read and searched no less. With 3 runs per arm on 3–5 minute jobs, this is within the noise seen in Gate 78 (2.3–3.9 min for one arm).
  - It would matter only if the map were built once per project and kept current (graphify's git hook), not per build.
  - It is not claimed.
- **Areas worked:** with one area per report, no builder duplicated another's work (Gate 78's free-text claims had).

## Setup

- **The job:** sqlglot 30.27.0 with 12 planted bugs (`referee/pick79.py`, seed 79), one small change each.
- **The builders' goal:** 11 users' bug reports, each showing what was run, what came out and what was expected, with no file or function named (`results/goal.md`, published now).
- **The hidden suite:** the 25 test methods those bugs break, run from sqlglot's own tests (`results/hidden_suite_and_bugs.json`, published now).
- **Arms**, each 4 builders through the product, with no owner and 30 minutes:
  - **H:** as shipped;
  - **HG:** plus the map in every clone, graphify's rule in `CLAUDE.local.md`, its PreToolUse hook in `.claude/settings.local.json` (all kept out of git), and graphify on the PATH.
- **Order:** H1, HG1, HG2, H2, H3, HG3, each alone.
- Predictions pushed before any run (`2258c2c`). Builders cost $8.82 in all.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| G1 | In each HG run, ≥ 3 of 4 builders run graphify | **Failed:** 3, 2, 1 |
| G2 | HG cost ≤ 0.85× H | **Failed:** 1.07× |
| G3 | HG time to accuracy ≤ 0.85× H | **Failed:** 0.88× |
| G4 | HG hidden ≥ H − 2 | **Held:** 24.7 vs 24.0 |
| G5 | HG reads and searches ≤ 0.8× H | **Failed:** 1.11× |
| Claim | G1 and (G2 or G3) and G4 | **Did not fire** |

## What changes in Hive

- **Nothing ships for the builders.** Following the registered rule for a failed G1, `hive/codemap.py` (the map and its guidance) stays off. graphify is not recommended to Hive's builders at this scale.
- **graphify stays in the lab** (`lab/graphify_lab.py`, Gate 78). There it answers questions grep cannot: which gates a function rests on, and what a gate built on.

## Limits

- Three runs per arm, on one codebase that the models partly know, with small planted bugs; jobs of 3–5 minutes on a 2-CPU machine.
- A codebase far larger than 85,000 lines, or one where symptoms do not grep to their cause, may differ. Neither is tested.

## Files

`prompts/PREDICTIONS.md`.

`referee/`:
- `pick79.py` (plant the bugs), `seed79.py` (build the job and the reports), `run79.py` (driver), `analyze.py`.

`results/<run>/`:
- the result (scores at every landing, cost, tool counts);
- the run log;
- the agents' accounts.

`results/goal.md`, `results/hidden_suite_and_bugs.json`, `results/analysis.txt`.
