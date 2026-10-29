# Gate 47 results: Claude and Codex in one swarm, Oct 29 2026

**Question** (from the user): "make the codex and claude swarms coordinate with each other", and test it. Also Codex as the lead that Gate 46 could not run.

**Answer.**
- **Yes. Claude and Codex builders coordinate through Hive's protocol as well as builders on one agent.**
  - Both mixed teams built the whole SQL engine from the 221-line skeleton: 1,340 of 1,340 visible tests and 100% of the hidden suite.
  - They took 9.2 and 8.1 minutes to reach 95%, against 7.5 (Claude only) and 8.3 (Codex only).
  - **No team broke main once** (corrected count, below).
  - Each agent did a real share of the work: Codex made 52% and 73% of the landings in the two mixed teams.
  - The registered ship rule fired: mixed swarms are a supported option (`hive start --agent claude,codex`).
- **Codex can lead.** The Codex lead put its plan on main in 85 seconds (the Claude lead took 75), pushed 3 updates as the Claude lead did, and its 6 Claude builders finished as fast as the Claude-led team's (8.0 vs 8.3 minutes). Its final `BRAIN.md` records the interfaces as built and places every category in a level. The lead's agent does not matter; Gate 46's verdict on leads (flat is faster) stands.

| Team | Builders | Time to 95% | Last landing | Visible | Hidden | Claude cost | Codex tokens | Landings (Claude / Codex) | Breaks of main |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | 2 Claude + 2 Codex | 9.2 min | 9.8 | 1,340 | 100.0% | $6.72 | 3.7 M | 16 / 17 | 0 |
| C | 4 Claude | **7.5 min** | 7.8 | 1,340 | 100.0% | $10.83 | – | 31 / – | 0 |
| X | 4 Codex | 8.3 min | 8.6 | 1,340 | 99.9% | $0 | 11.9 M | – / 51 | 0 |
| LX | Codex lead + 6 Claude | 8.0 min | 8.2 | 1,340 | 99.8% | $13.31 | 0.75 M (lead) | 23 / – | 0 |
| LC | Claude lead + 6 Claude | 8.3 min | 8.3 | 1,340 | 99.9% | $12.82 | – | 38 / – | 0 |
| M2 | 2 Claude + 2 Codex | 8.1 min | 8.7 | 1,340 | 100.0% | $5.74 | 5.3 M | 13 / 36 | 0 |

What we learned beyond the predictions:
- **Codex builders land smaller, more often.** The Codex-only team made 51 landings against Claude's 31 for the same work; in M2 the two Codex builders made 36 of 49.
- **Mixing halves the Claude bill.** A mixed team cost $5.74–6.72 of Claude against $10.83 for Claude alone. Codex runs on the owner's ChatGPT plan, so its share has no per-run price. That is the practical reason to mix: two subscriptions' worth of builders, each agent's limit lasting twice as long.
- **Both agents hit the same tool snag and fixed it the same way.** The lab's `tools/land.py` needed a Python 3.11.2 workaround in this container. A Claude builder and a Codex builder each patched it independently, and neither broke the other's patch.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| P1 | Both mixed teams reach 95% within 45 minutes | **Held:** 9.2 and 8.1 min |
| P2 | Both mixed teams break main at most once | **Held:** 0 and 0 (the registered script printed 1 each, an artifact; see below) |
| P3 | In both mixed teams each agent lands ≥ 25% | **Held:** Codex 52% and 73% |
| P4 | Mean t95 of M ≤ 1.15 × the mean of C and X | **Held:** 8.7 vs 1.15 × 7.9 = 9.1 |
| P5 | Codex builders slower: t95 X ≥ 1.2 × C | **Failed:** 1.11× |
| P6 | All six teams' hidden pass within 3 points | **Held:** 0.2 points |
| P7 | The Codex lead's plan on main within 6 minutes | **Held:** 85 s |
| P8 | t95 LX within 20% of LC | **Held:** 8.0 vs 8.3 |
| Ship | P1 and P2 | **Fired** |
| Kill | | **Did not fire** |

## Analysis error (disclosed)

The registered `analyze.py` replayed the seed's own history as if it were team work:
- 15 commits from Gates 1 and 2, the last at 362 passing tests;
- the seed's final commit cut the engine back to the 9-test skeleton, but it is authored `hive`, and the replay skips that author;
- so every team's first landing (9 tests) looked like a fall from 362 to 9.

That made one false "break" per team (charged to whoever landed first) and 15 unattributed landings. The verdicts do not change: P2 held either way. `referee/recount.py` (written after the run) counts only each team's own commits, from 9 tests. Its output is in `results/recount.txt`; the table above uses it.

## Setup

- **Project:** Gate 46's deep project and prompts, unchanged.
- **Machine:** the lab container, 24 CPUs. Claude Code 2.1.311 and Codex 0.160.1, on the user's own logins.
- **Teams:** run alone, one after another: M1, C, X, LX, LC, M2. Mixed teams: w1 and w3 on Claude, w2 and w4 on Codex.
- **Hidden suite:** gen2.py, seed 5000000, generated privately in the container. 11 categories are left out where this container's SQLite disagrees with the stored answers (Gate 43's rule; Gate 46's machine left out 3). 2,080 tests are scored.

## Limits

- One run per team (two for M), one project.
- The flat teams had 4 builders and the lead teams 7, so C/X/M are compared with each other and LX only with LC.
- The project builds in 8–10 minutes, so differences of a minute are within noise: in Gate 46, two identical teams differed by 1.9 minutes.
- Codex's cost is not in dollars.

## What changes in Hive

- `hive start --agent claude,codex` mixes agents; each builder takes the next agent in turn. `agents.csv` records each builder's agent, and `hive doctor` checks every agent in the mix is installed.
- The README lists it.
- The lab launcher takes `--mix` the same way.

## Files

`prompts/` (Gate 46's prompts and these predictions), `referee/` (driver, registered analysis, recount), and `results/`:
- `analysis.txt`, `recount.txt`;
- per-team summaries with progress after every commit (`teams_summary.json`), and `agents.csv` with each builder's agent;
- each agent's final report (`final_messages.md`);
- both leads' outputs and final brains;
- the run log;
- all six teams' git histories (`swarms/`).
