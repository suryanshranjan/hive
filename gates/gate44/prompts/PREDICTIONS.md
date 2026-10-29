# Gate 44 predictions: Hive's rules and a talking swarm, together

Registered Oct 29 2026, before the rules exist. The user asked whether the two ideas together beat either alone. Gate 38 is untouched.

## Why this test

Two results from last night:
- **Gate 42:** the rule sheet written from the first build's code and corrected by the owner took builders from 38.8% to 99.6%.
- **Gate 43:** a shared message board changed nothing on a project with no hidden rules: same finish, cost and correctness.

Talking could still matter in an intent project in two ways:
- **Without rules,** talking might make a team guess *consistently* (one reading of rounding or NULL for all functions). That could help or hurt.
- **With the corrected sheet,** talking might help builders apply rules that span functions. With 99.6% already, there is almost nothing left to gain.

## Setup

- **Rules and suites:** a fresh independent rule-giver (Gate 39's brief: 10 functions, 25 declared decisions). Visible seed 44100; hidden 250 tests (seed 44200000), never committed.
- **Stage 1:** N0 builds (3 builders, silent, spec and examples only).
- **The code sheet (as Gate 42):** a describer reads and runs N0's code (never the oracle) and writes every behaviour as a rule. The synthetic owner reviews it through Hive's `confirm_sheet`: he marks what is wrong, says it right and adds what is missing.
- **Stage 2 teams** (3 builders each, fresh from the starting repo, no questions):
  - **NT:** no rules, talking.
  - **C:** the corrected sheet, silent.
  - **CT:** the same corrected sheet in the same words, talking.
- **Talking:** Gate 43's board (`board.py`) and a prompt asking for high-level coordination: how each builder reads the open parts of the spec, rules worked out, pitfalls, answers to questions. The talking prompt differs from the silent one only there (`prompt_builder_talk.md`).
- **Analysis:** `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| P1 | C ≥ 95% (Gate 42 replicates) | 70% |
| P2 | Talking adds nothing on top of the sheet: \|CT − C\| ≤ 3 points | 75% |
| P3 | Talking does not replace the rules: \|NT − N0\| ≤ 8 points | 70% |
| P4 | Each talking team posts ≥ 3 messages | 70% |
| P5 | CT costs ≤ 1.10 × C | 70% |

## Decision rules

- **Ship talking:** CT − C ≥ +3 and NT − N0 ≥ +5.
- **Kill for talking:** CT ≤ C and NT ≤ N0. Hive stays silent.

## Limits

- One run per team, 3 builders each, 10 functions. Differences under about 8 points between NT and N0 are noise.
- N0 runs alone in stage 1; the others run together in stage 2. Correctness, not time, is the measure.
- Synthetic owner, as in Gates 39–42.
- About $6.
