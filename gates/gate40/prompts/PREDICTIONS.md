# Gate 40 predictions: unusual input as owner decisions

Registered Oct 29 2026, before the rules exist. Gate 38 is untouched: no founder, no Telegram, none of its files.

## Why this test

Gate 39 put Hive's interview in a wind tunnel. A synthetic owner held the exact rules. Given his complete rule sheet, builders passed 250 of 250 hidden tests. Hive's interview reached 76%. Of 25 decisions, 8 were never asked, and **all 8 were about unusual input**: an unreadable date, letter case, separators, leftover fractions. Hive's planner is told to list "business outcomes, not technical choices", and it treated these as technical. Yet each one is what a receipt, a report or a customer sees.

The change under test (`hive/interview.py`, `inputs=True`): the planner also lists what the product shows for unusual input, business outcomes first, and the interview may ask up to 30 questions instead of 20. It ships as the default only if it wins here.

Gate 39's fixes are in both interview arms: corrections amend rules; the terminal restates a rule before its correction; own words keep their detail. The harness defect is fixed too: the owner now sees his whole terminal history.

## Setup

- **Rules:** a fresh independent rule-giver with Gate 39's brief: 10 functions, 25 declared decisions, one worked example per decision. Kept private until scored.
- **Suites:** visible seed 40100; hidden 250 tests (seed 40200000, 25 per function, 70% edge). Never committed.
- **Synthetic owner:** as in Gate 39 (`prompts/owner_brief.md`); one headless call per prompt, holding the rules and able to run them, seeing his terminal.
- **Teams** (3 builders each, no questions):
  - **N0:** spec and examples only.
  - **H:** rules from Hive's interview as it now ships (planner skips unusual input, up to 20 questions).
  - **H2:** rules from the same interview with `inputs=True` (unusual input listed, up to 30 questions). A separate interview, same owner.
  - **R:** the owner's complete rule sheet (replication of Gate 39's ceiling).
  - **T:** the owner's decision tour (replication of R against T).
- **Judge** (before any build): per declared decision, asked in H, asked in H2, and how sheets H, H2 and R state it.
- **Analysis:** `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| G1 | Coverage: H2 asks about ≥ 85% of the 25 decisions; H asks about ≤ 75% | 50% |
| G2 | H2 − H ≥ +8 points hidden | 45% |
| G3 | Transfer (asked decisions stated right on the sheet) ≥ 0.85 in both H and H2 (Gate 39's fixes work; Gate 39: 0.76) | 55% |
| G4 | R ≥ 95% (the complete sheet's ceiling replicates; Gate 39: 100%) | 75% |
| G5 | R − T ≥ +10 points (complete words beat one example per decision again; Gate 39: +24.4) | 55% |
| G6 | H2's owner replies ≤ 1.6 × H's (the cost of the extra coverage in owner effort) | 60% |
| G7 | N0 below 65% | 85% |
| Kill | H2 ≤ H: asking about unusual input does not ship | 25% |

**Power note (before the run):** H2 − H is paired over 10 functions. Gate 39's per-function spread puts its 95% interval near ±10 points, so G2 is a point prediction that the interval may not confirm. The coverage and transfer labels (G1, G3) are the mechanism check; the hidden score is the outcome.

## Decision rules

- **H2 − H ≥ +5 and H2's coverage above H's:** the planner lists unusual input by default (`inputs=True`, up to 30 questions).
- **Coverage rises but the score does not:** the extra answers do not reach the builders. Look at transfer and the sheet before shipping anything.
- **R < 95%:** the complete-sheet ceiling of Gate 39 was luck on one rule set. Say so in BRAIN.

## Cost and limits

- About $10: 15 builders (about $0.2 each on this session's model), 2 interviews (about $2 to $3 each), the rule-giver, the documenter and the judge.
- One run per team; one interview per interview arm, so H against H2 also carries each interview's own luck.
- The owner is synthetic and perfectly consistent; a real owner may tire at 30 questions (Gate 37: 2–5 s per answer after the 12th).
