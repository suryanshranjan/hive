# Gate 44 results: Hive's rules and a talking swarm, together, Oct 29 2026

**Question** (from the user). Do Hive's rules (the corrected code sheet, Gate 42) and a talking swarm (Gate 43's message board) do better together than either alone?

**Answer.**
- **No. The rules do all the work; talking adds nothing on top.**

| | Silent | Talking | Talking adds |
| --- | --- | --- | --- |
| No rules | 45.2% (N0) | 49.2% (NT) | +4.0 (CI 0.0 to +11.6) |
| Corrected code sheet | **100%** (C) | **100%** (CT) | +0.0 |
| **The sheet adds** | **+54.8** (CI +40.4 to +68.8) | **+50.8** | |

- **Without rules,** talking helped a little, inside the noise. The board shows why it can't help much: builders announced their *guesses* ("readings, guesses: star rating nearest 0.5, votes < 10 → NULL…") and agreed on conventions ("NULL in → NULL out everywhere"). A consistent guess is still a guess. NT fixed 9% of N0's edge errors; the sheet fixed 100%.
- **With the sheet,** both teams passed 250 of 250. Talking was used for dividing the work ("w2 please take ship_cost, sku_clean"), which the claim files already do. Cost was the same ($0.70 vs $0.73).
- **The code sheet replicated:** Gate 42 gave 99.6%; here it gave 100%, on a new rule set.

## Setup

- **Rules.** A fresh independent rule-giver (Gate 39's brief): 10 functions, 25 declared decisions. Predictions pushed before the rules existed (`69fd49a`).
- **Suites.** Visible seed 44100; hidden 250 tests (seed 44200000, 70% edge calls), not committed.
- **Stage 1:** N0 builds (3 builders, silent, spec and examples).
- **Code sheet:**
  - The describer read N0's code and wrote 66 rules ($0.33).
  - The synthetic owner marked 40 of them wrong, said each one right, and added what was missing: 67 rules, $3.91.
  - C and CT got these rules in the same words.
- **Stage 2:** NT, C and CT, 3 builders each. Talking teams had `board.py` and a prompt asking for high-level coordination; that is the only difference from the silent prompt.

| Team | Builder cost | Hidden tests | 95% CI by function | Messages |
| --- | --- | --- | --- | --- |
| N0 | $0.59 | 113/250 (45.2%) | 31.2–60.0% | – |
| NT | $0.60 | 123/250 (49.2%) | 33.6–65.6% | 5 |
| C | $0.73 | 250/250 (100%) | 100–100% | – |
| CT | $0.70 | 250/250 (100%) | 100–100% | 5 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| P1 | C ≥ 95% | **Held:** 100% |
| P2 | \|CT − C\| ≤ 3 | **Held:** 0.0 |
| P3 | \|NT − N0\| ≤ 8 | **Held:** +4.0 |
| P4 | Each talking team posts ≥ 3 messages | **Held:** 5 and 5 |
| P5 | CT costs ≤ 1.10 × C | **Held:** 0.96× |
| Ship talking | CT − C ≥ +3 and NT − N0 ≥ +5 | **Did not fire** |
| Kill for talking | no gain with or without rules | **Did not fire** (NT +4.0, inside noise) |

All five predictions held.

## What it means

1. **Hive's value is getting the owner's rules in, not getting builders to talk.** Across Gates 43 and 44, talking moved results by 0 to 4 points; the rules moved them by 55.
2. **Talking spreads what builders already know.** Without the owner, what they know is guesses. With the owner's sheet, they already share everything that matters through it.
3. **Hive stays silent.** If talking is ever revisited, its one plausible place is a large, tightly coupled codebase where one builder's change to a shared part breaks others (untested).

## Limits

- One run per team, 3 builders, 10 functions, synthetic owner. NT − N0 (+4.0) is within the noise this design can see (about ±8).
- N0 ran alone in stage 1; the others ran together in stage 2. Correctness, not time, was measured.

## Files

`prompts/` (silent and talking builder prompts, owner and describer briefs, predictions), `board.py`, `referee/` (sheet step, analysis, unsealed oracle), `results/` (summary, analysis, probes, costs, the code sheet and review, both boards, run log), `swarms/`, `logs/`.
