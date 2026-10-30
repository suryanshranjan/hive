# Gate 61 predictions: the flight log (do confirmed outcomes survive the next build?)

Registered Oct 30 2026, before the run. Asked for by the user ("Run the tests as required", after the proposal "a flight log that grows"). Gate 45 and the founder's Telegram are untouched.

## Why this test

Every hand-over so far ends when the owner's corrections reach the code. Hive keeps them as rulings in text (`hive rules`), which the next build's builders are told about. Nothing *executable* keeps them. A later build can undo a decision the owner confirmed without anyone noticing, and the owner would have to check it all again.

The flight log keeps every outcome the owner confirmed as a test in the project's suite, where the landing guard refuses any change that breaks it. This gate asks whether that matters: in follow-on work that touches the old code, how much confirmed behaviour do builders break without the log, and does the log stop it?

## Setup

- **Build 1:** Gate 55's CC build. Its owner reviewed every rule carefully, and it passed 100% of Gate 55's hidden suite. It is probed again on a new hidden suite (seed 61200000). Its ten functions sit in three files written by three different builders, each with its own input handling.
- **The flight log:** Gate 58's spotter (now also writing the table setup for the aggregate) writes concrete cases from build 1. The cases whose outcome matches the policy stand in for a careful owner's confirmations; the referee checks them with the oracle. They become tests in `tests/visible/` (ids `<function>_fNN`), the folder the landing guard checks.
- **Build 2, the next week** (`prompts/prompt_refactor.md`):
  - clean up the ten functions into one module with shared helpers for input and rounding, **without changing what any function does**;
  - add `invoice_total` (bulk price plus the late fee on it; 2 example tests).
- **Teams:** six teams of 2 builders each, run 6 at a time in the order N1, T1, T2, N2, N3, T3.
  - **N1–N3:** the suite as before: the 1,340 engine tests and 2 examples per function.
  - **T1–T3:** the same, plus the flight log, and one line in the README saying last week's confirmed outcomes are kept as tests.
- **Scores (`referee/run61.py`):**
  - each team's hidden pass on the ten old functions;
  - **broke:** the hidden calls build 1 had right that build 2 gets wrong;
  - `invoice_total` on 60 calls;
  - whether the clean-up was done.

  `referee/analyze.py` applies the rules below. Both scripts are committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| F1 | At least one N team breaks ≥ 2% of the hidden calls build 1 had right | 55% |
| F2 | T's mean broke share is at most half of N's | 45% |
| F3 | T's mean hidden pass on the old functions ≥ N's + 2 points | 40% |
| F4 | All 6 teams finish the clean-up (`business.py` exists; the three old files are gone) | 50% |

## Decision rules

- **Ship:** F2 and F3 hold. Hive keeps every outcome the owner confirms (spot checks and re-shows) as a test in the project's suite after the hand-over.
- **Kill:** N's mean broke share is under 1%. Then builders do not break confirmed behaviour in follow-on work at this scale, and the log is not needed for survival. Its other use, asking the owner less on later builds, is not tested here.
- **Otherwise:** report what broke and where, with no product change.

## Limits

- One clean-up task on one codebase. Build 1 is a careful owner's build, and the flight log's confirmations come from the oracle, not a person. The log covers what the spotter thought to check, not every decision.
- About $5.
