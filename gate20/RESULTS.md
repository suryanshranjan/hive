# Gate 20 results: the founder's own examples, and the company's documents, on the real rules, Oct 27 2026

Only aggregate numbers are published. The rules, the founder's examples and the company's documents stay private (Company X; see Gate 7).

**Question.** On the real rules, agent-drafted examples that the owner only confirmed did no better than builder questions (Gate 18: 0.93×). Does it help when the **founder writes the examples himself**? And do the company's **real policy documents** add anything on top?

**Answer.**
- **The founder's own examples did better than the agent-drafted ones, but not by the registered margin over questions.** They lifted hidden correctness from 23.6% to **72.4%** (+48.8 points; Gate 18's agent-drafted examples +38.8), and fixed **1.17×** the edge errors 19 builder questions fixed (Gate 18: 0.93×; registered target 1.3×). O1 failed; O2 held.
- **Examples + questions reached 83.6%; with the company's documents too, 84.8%,** the best on these rules (Gate 7: 49.6%; Gate 18: 78.0%).
- **The documents settle what they say, and nothing else.** Only 2 of the 10 functions' rules are written down anywhere in the workspace. On those 2, the team with the documents fixed **all** of N0's edge errors (1.00, against 0.90 without them; O7 held). On the other 8, the documents changed nothing (0.84 and 0.84). Overall they added +1.2 points (CI −4.0 to +7.2; O6 failed).
- **The founder pointed where an agent points about half the time:** 31 of the 58 examples (53%) were exactly inputs on the agent-drafted QA list (measured before the run).

## Setup

- **Rules.** Gate 7's 10 real functions as confirmed by the founder; Gate 18's neutral one-line specs.
- **The founder's examples.** 58 inputs (5 or 6 per function), written without looking at the QA list, the check table or the rules; outputs come from the confirmed rules. The 31 that equal a QA-list input were kept, and those inputs were removed from the hidden and visible pools for every team (fair copy rule).
- **The company's documents** (amendment, registered before the run). A Notion search found policy text for only 2 of the 10 functions. Those sections (808 words, verbatim) became `HANDBOOK.md` for team HTQ.
- **Teams** (3 builders each): **N0**; **T** (founder's examples); **Q** (19 questions); **TQ** (both); **HTQ** (documents + examples + 19 questions).
- **Hidden suite.** 250 tests (25 per function, seed 20200000), 70% edge calls drawn from the remaining 94 QA cases.
- Predictions pushed before the run (commits 6387bbf and 4ff59b7).

| Team | Questions used | Builder cost | Visible | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | 0 | $1.68 | 1,360/1,360 | **23.6%** | 15.2–32.4% | |
| Q | 18 of 19 | $1.95 | 1,360/1,360 | **59.2%** | 39.6–79.2% | +35.6 (CI +13.6 to +57.6) |
| T | 0 | $2.12 | 1,380/1,380 | **72.4%** | 54.8–88.4% | +48.8 (CI +31.6 to +66.4) |
| TQ | 19 of 19 | $1.69 | 1,380/1,380 | **83.6%** | 67.2–96.8% | +60.0 (CI +42.8 to +76.0) |
| HTQ | 18 of 19 | $1.86 | 1,380/1,380 | **84.8%** | 70.8–96.0% | |

Total $9.30 at list price (no rule-giver). All 15 workers exited without API errors.

## Predictions scored (registered code: `gate18/referee/analyze.py`, `referee/analyze_htq.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| O1 | fixed_T / fixed_Q ≥ 1.3 | **Failed**: 217 / 185 = **1.17** |
| O2 | T − N0 ≥ +38.8 | **Held**: +48.8 |
| O3 | TQ ≥ 80% | **Held**: 83.6% |
| O4 | Q and TQ use ≥ 17 of 19; T and TQ pass every example test | **Held**: 18 and 19; all visible tests pass |
| O5 | N0 below 70% | **Held**: 23.6% |
| O6 | HTQ − TQ ≥ +3 | **Failed**: +1.2 (CI −4.0 to +7.2) |
| O7 | On the 2 documented functions, HTQ fixes ≥ 0.9 of N0's edge errors and ≥ TQ + 0.1 | **Held**: 1.00 against 0.90 |
| Rule | O1 ≥ 1.3: owners write examples themselves | **Did not fire** |
| Rule | O1 < 1.1: generate examples, owners only confirm | **Did not fire** (1.17 is between) |

## What it means

### 1. Who points: founder vs agent, on the same real rules

| | Gate 18: agent-drafted, owner-confirmed | Gate 20: founder-written |
| --- | --- | --- |
| Examples | 56 | 58 |
| Examples alone, vs N0 | +38.8 | **+48.8** |
| Edge errors fixed, examples / questions | 0.93 | **1.17** |
| Calls broken (right in N0, wrong after) | examples 26, questions 60 | examples **5**, questions 34 |
| Examples + questions | 78.0% | **83.6%** |

The hidden suites differ between the two gates (Gate 20 removes the founder's 31 overlapping inputs), so this is a comparison across gates, not a controlled one. The direction is consistent, though: the founder's own points carried more intent and broke far less. The gap is smaller than with agent owners (Gate 13: 2.7×), partly because the founder and the agent picked the same inputs half the time.

### 2. Documents: exact where they speak, silent elsewhere

| Functions | N0 edge errors | TQ fixed | HTQ fixed |
| --- | --- | --- | --- |
| Documented (2) | 51 | 0.90 | **1.00** |
| Not documented (8) | 238 | 0.84 | 0.84 |

A real company's written policy covered 2 of 10 functions. Where it spoke, it closed the last gap; elsewhere it was neutral, and unlike Gate 16's agent-written handbook it did not mislead. The bottleneck for a real owner is the undocumented 80%, which only the founder's examples and answers reach.

## Design consequences for the product

1. **Ask the owner for their own examples** (one per rule they know), and generate suggestions for them to confirm alongside. The founder's own examples beat the agent's (+48.8 vs +38.8) and broke far less, while overlapping half the time. The registered rule was undecided (1.17 sits between 1.1 and 1.3), so the product should support both.
2. **Read the company's documents, but expect them to cover little.** Here they covered 2 of 10 functions and settled those completely.
3. **Always add builder questions:** +11.2 points on top of the founder's examples (CI +3.2 to +20.4).

## Limits

- One run per team, 10 functions; wide intervals.
- One founder and one company.
- The founder's examples reflect some superseded rules from before Gate 7's document check; inputs only were used, with answers from the confirmed rules.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions, decision rules and the documents amendment, pushed before the run |
| `referee/analyze_htq.py` | Registered aggregate-only analysis for the documents team |
| `results/summary.md`, `results/analysis.txt` | Arm-level numbers only |
