# Gate 41 predictions: keep every ruling whole

Registered Oct 29 2026, before the rules exist. Gate 38 is untouched: no founder, no Telegram, none of its files.

## Why this test

Over two rule sets, builders given the owner's complete rule sheet passed 500 of 500 hidden tests (Gates 39, 40). Hive's interview delivered about half of its decisions whole:
- its questions were about roughly 70% of the decisions;
- its sheet then stated right only 0.69 to 0.76 of those.

The sheet step merges every answer into one general rule per function (about 11 rules), and branches drop out. Questions skipped as "settled by an earlier answer" lose more.

The candidate fix changes only the hand-over, so one interview can feed both arms. That removes the interview's luck, which dominated Gate 40.
- **H:** the general sheet, as `hive start` gives it today.
- **K:** the same sheet, plus his answer to each situation kept whole. These are the rules list before the merge: "situation → his choice", or his own words as confirmed or amended (`interview.instructions(rules, rulings)`).

The judge also labels whether his own answers stated each decision right, which splits the loss into the owner's wording against Hive's merge. It reads skipped questions from the terminal.

## Setup

- **Rules:** a fresh independent rule-giver with Gate 39's brief (10 functions, 25 declared decisions). Kept private until scored.
- **Suites:** visible seed 41100; hidden 250 tests (seed 41200000, 70% edge). Never committed.
- **One interview**, as shipped, with Gate 40's harness (the owner sees his whole terminal).
- **Teams** (3 builders each, no questions):
  - **N0:** spec and examples.
  - **H:** the interview's sheet.
  - **K:** the sheet plus every ruling kept whole.
  - **R:** the owner's complete rule sheet (third replication of the ceiling).
- **Judge** (before any build): for each declared decision:
  - asked (an answered question is about it), or in skipped questions only;
  - whether his answers state it right;
  - how hand-overs H, K and R state it.
- **Analysis:** `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| K1 | K − H ≥ +5 points hidden | 50% |
| K2 | Of the asked decisions, K states ≥ 0.90 right and H ≤ 0.80 | 50% |
| K3 | K breaks at most 5 more of N0's correct edge calls than H (whole rulings do not cause extra stretching; Gates 4 and 28 saw answers stretched) | 60% |
| K4 | R ≥ 95% (third replication) | 80% |
| K5 | His answers state ≥ 0.85 of the asked decisions right: the loss is in Hive's hand-over, not in his wording | 55% |
| K6 | N0 below 65% | 85% |
| Kill | K ≤ H: keeping rulings whole does not help | 30% |

**Power note:** H and K share the interview, so their difference is the hand-over plus builder noise. Gates 39 and 40 put builder noise on a function near ±10 points, so the interval on K − H will be about ±8. K2 and K5 are the mechanism checks.

## Decision rules

- **K − H ≥ +5:** `hive start` hands builders the sheet plus every ruling whole (`interview.instructions(rules, rulings)`); the interview returns both.
- **K5 fails** (his answers themselves miss): the loss is in the questions and his wording. The next fix is a question that asks for the whole rule of a decision, not one case of it.
- **R < 95%:** the ceiling is not as firm as two runs suggested. Say so in BRAIN.

## Cost and limits

- About $6: 12 builders at about $0.2 each, one interview (about $2), the rule-giver, the documenter and the judge.
- One interview, one run per team, synthetic and perfectly consistent owner, same model family throughout.
