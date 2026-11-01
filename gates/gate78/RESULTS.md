# Gate 78 results: a map of the codebase for the swarm (graphify), Nov 1 2026

**Question** (the user: "use graphify … use good qualities of it, will help in both scopes"). On a large real codebase, does one shared map of the code (graphify), built once before launch, make Hive's swarm cheaper or faster without making it less right?

**Answer.**
- **Not shown: no builder used the map.** In both map runs, all 8 builders ignored it: no `graphify` command, and no look at its report. M1 failed.
- **The registered claim formula "held", but in substance it did not.** The map arm was cheaper (0.77×), sooner (0.80×) and passed more hidden tests (57.5 vs 53.0 of 61), but these differences cannot come from a map nobody opened. They are two runs per arm of a 3-minute job, where one builder doing nothing (HM1's w2, $0.13) moves the mean.
- **Following the registered rule for a failed M1, the map does not ship.** It stays off behind `code_map` / `HIVE_CODE_MAP=1`. The open question is now how to put it in front of builders, not whether it helps.

| Run | Hidden (of 61) | Time to ≥ 55 | Wall | Builders' cost | Reads and searches per builder | graphify calls |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | 53 | never (2.9) | 2.9 min | $1.51 | 15.2 | – |
| HM1 | 58 | 1.9 min | 2.3 min | $1.08 | 11.5 | 0 |
| HM2 | 57 | 2.8 min | 3.9 min | $1.34 | 13.8 | 0 |
| H2 | 53 | never (3.0) | 3.0 min | $1.63 | 17.5 | – |
| **H mean** | **53.0** | 3.0 min | | **$1.57** | 16.4 | |
| **HM mean** | **57.5** | 2.3 min | | **$1.21** | 12.6 | 0 |

- **Why nobody needed a map:** the job was too easy to find one's way in.
  - The goal named each function's file, so builders found every one with `grep NotImplementedError` and `sed -n`.
  - sqlglot is well known to the models. Four builders rebuilt 12 functions of an 85,000-line codebase in 2–4 minutes.
  - A map pays where finding the code is the work: a goal in the owner's words, on code nobody has seen. This job did not have that.
- **Building the map cost 46 seconds before launch** (tree-sitter extraction of 7,401 nodes and 23,283 edges, then one Haiku call to name its 206 groups). The table's times start at launch, without it. Counted from the start, the map arm was no sooner (about 3.1 vs 3.0 min).
- **Observed: without configured areas, builders duplicate work.**
  - The seed's `.hive/config.json` had no areas, so claim names were free text. Two builders often claimed the same functions under different names (H1: `w2core` and `w3`; HM2: `all` and `w1a`) and rebuilt them twice.
  - In HM1, one builder claimed `all12` while working on half; another builder saw that and stopped.
  - This hit both arms. Hive configures areas when it knows the parts (`hive start`).

## Setup

- **The job:** sqlglot 30.27.0 (MIT, from PyPI; 85,000 lines; not installed on this machine), with 12 module-level functions in 10 files emptied. They were chosen by `referee/pick78.py` (seed 78) from 304 candidates.
- **The hidden suite:** the 61 test methods (of 1,179 in the fast suite) that then failed, removed from the visible repo by `referee/seed78.py` and run from sqlglot's own test files. Now published in `results/hidden_suite.json`.
- **Arms**, each 4 builders through `hive.swarm.prepare` and `launch`, with no owner and 30 minutes:
  - **H:** as shipped;
  - **HM:** plus the map (`hive/codemap.py`) in every clone and a paragraph in the prompt telling builders to ask it.
- **Order:** H1, HM1, HM2, H2, each alone.
- Predictions pushed before any run (`9cb1d99`). Builders cost $5.56 in all.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| M1 | In each HM run, ≥ 3 of 4 builders use graphify | **Failed:** 0 and 0 |
| M2 | HM cost ≤ 0.85× H | Held by the formula (0.77×), **not caused by the map** |
| M3 | HM time to accuracy ≤ 0.85× H | Held by the formula (0.80×; launch only), **not caused by the map** |
| M4 | HM hidden ≥ H − 3 | Held (57.5 vs 53.0) |
| M5 | HM reads and searches ≤ 0.8× H | Held by the formula (0.77×), **not caused by the map** |
| Claim | (M2 or M3) and M4 | **Held by the formula, failed in substance:** M1's rule governs |

## Disclosed

- **A measurement bug, fixed after the runs.** The driver first looked for builders' transcripts with only `/` and `.` replaced by `-` in the path. Claude Code replaces every non-alphanumeric character, including `_`, so every tool count read 0. The tool counts were recounted from the same transcripts (`run78.py --tools-only`); no score changed.
- **One "leak" flag is a false positive:** a builder copying a test file to its own temporary folder, whose path contains "scratchpad". No builder reached another copy of sqlglot.

## What changes in Hive

- **Nothing ships.** `hive/codemap.py` stays, off by default, with a test.
- **The lab gained a map of its own** (`lab/graphify_lab.py`, the research scope). It joins Hive's code to the 78 gates with edges read from the repo:
  - a gate to the earlier gates it builds on (220 edges);
  - a gate to the product files it shipped in (133);
  - a function to the gates it cites (175).

  `graphify explain "Gate 74"` shows what the gate found, what it built on and where it lives in the code, without reading 450 lines of BRAIN.md.
- **Next, for the product:** test the map where finding the code is the work, and put it where builders cannot miss it:
  - a goal in plain words, without file names, on code the models do not know;
  - graphify's own Claude Code hook, which steers searches to the map.

## Files

`prompts/PREDICTIONS.md`.

`referee/`:
- `pick78.py` (choose the functions), `seed78.py` (build the job), `run78.py` (driver, scoring, tool counts), `analyze.py`.

`results/<run>/`:
- the result (scores at every landing, cost, tool counts);
- the run log;
- the agents' accounts.

`results/hidden_suite.json`, `results/analysis.txt`.
