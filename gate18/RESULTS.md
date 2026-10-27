# Gate 18 results: worked examples on a real company's rules, Oct 27 2026

Only aggregate numbers are published. The rules belong to a real company (Company X, anonymous; see Gate 7). The oracle, specs, cases, probes, questions, answers, logs and histories are kept privately by the user.

**Question.** Gates 13 to 17 found that owner-given worked examples carry intent far better than builder questions, but every rule set there was written by an agent. Does that hold on a real company's rules?

**Answer.**
- **Worked examples carry real intent.** On Company X's 10 rules, 56 owner-confirmed examples lifted hidden correctness from **26.0% to 64.8%** (+38.8 points). With 19 questions on top, **78.0%**, against 49.6% for Gate 7's best on the same rules.
- **But here they did not beat builder questions of the same size.** 19 builder questions (up to 57 values) reached 56.4% and fixed slightly *more* edge errors than the 56 examples (184 against 171; ratio 0.93). R2 failed.
- **That fits the pointer finding instead of breaking it.** These examples were not chosen by the owner. They were QA cases drafted by an agent in Gate 7 and confirmed row by row by the owner, which is the same kind of pointing builders do. Gates 13 to 17's examples were chosen by the owner who wrote the rules. A plausible reading (conjecture): the advantage comes from *who chooses the points*, and confirmation alone does not supply it.
- R1, R3 and R5 held; R2 failed; R4 failed narrowly (one team used 16 of 19 questions).

## Setup

- **Rules.** Gate 7's 10 real functions, as confirmed by the owner against the company's documents, wrapped privately. No rule-giver.
- **Examples.** Gate 7's QA edge cases (the owner checked each row) were split per function by a fixed shuffle (`random.Random(18000)`): 56 became visible tests for teams T and TQ (21 test files), and 60 stayed as the hidden suite's edge inputs. 5 of the 60 (8%) are strict near copies of an example input.
- **Specs.** Gate 7's original one-line specs were not available, so new neutral ones were written: purpose and argument names only, no rules, thresholds or allowed values. They are the same for every team.
- **Teams** (3 builders each): **N0**; **T** (examples); **Q** (19 questions for the team); **TQ** (examples and 19 questions). Predictions and the aggregate-only analysis were pushed before the run (commit 1c1f661).
- **Hidden suite.** 250 tests (25 per function, seed 18200000), 70% edge calls.

| Team | Gets | Questions used | Builder cost | Visible | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| N0 | nothing | 0 | $1.54 | 1,360/1,360 | **65/250 (26.0%)** | 14.4–39.6% | |
| Q | 19 questions | 19 of 19 | $1.59 | 1,360/1,360 | **141/250 (56.4%)** | 40.0–72.4% | +30.4 (CI +10.0 to +49.6) |
| T | 56 examples | 0 | $1.79 | 1,381/1,381 | **162/250 (64.8%)** | 48.0–80.8% | **+38.8** (CI +25.2 to +53.6) |
| TQ | both | 16 of 19 | $1.72 | 1,381/1,381 | **195/250 (78.0%)** | 63.6–90.8% | **+52.0** (CI +38.8 to +66.4) |

Total $6.64 at list price (no rule-giver). All 12 workers exited cleanly, in 1.4 to 2.2 minutes (10 functions instead of 20).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| R1 | T − N0 ≥ +20 | **Held**: +38.8 |
| R2 | fixed_T / fixed_Q ≥ 1.3 | **Failed**: 171 / 184 = **0.93** |
| R3 | TQ ≥ 75% | **Held**: 78.0% |
| R4 | Q and TQ use ≥ 17 of 19; T and TQ pass every example test | **Failed** narrowly: Q 19, TQ 16. Example tests all pass |
| R5 | N0 below 70% | **Held**: 26.0% |
| Kill | T − N0 < +10 | **Did not fire** |
| Rule | R1 and R3 hold: worked examples are confirmed on real rules | **Fired** |

## What it means

### 1. Examples help on real rules, and stack with questions

| | Hidden pass | Edge errors fixed (of 252) | Calls broken (right in N0, wrong here) |
| --- | --- | --- | --- |
| Q | 56.4% | 184 (0.73) | 60 |
| T | 64.8% | 171 (0.68) | **26** |
| TQ | **78.0%** | **220 (0.87)** | 27 |

Examples fixed slightly fewer errors than questions but broke far fewer calls (26 against 60), so T still passed more hidden tests (+8.4, CI −9.6 to +24.8). Questions on top of examples added +13.2 (CI +4.0 to +23.6).

### 2. Why the examples lost their edge here (two explanations, not separable in this run)

| | Gates 13–17 | Gate 18 |
| --- | --- | --- |
| Who chose the example inputs | the owner who wrote the rules | an agent (Gate 7's QA drafter); the owner confirmed them |
| Questions per function | 0.85 (17 for 20) | 1.9 (19 for 10) |
| Examples / questions ratio, edge errors fixed | 2.7 (Gate 13) | 0.93 |

- **Who points (the conjecture this lab favours):** agent-drafted QA cases sit in the region a careful engineer imagines, the same region builder questions explore (Gate 12). Confirming them adds correct answers but not new places to look.
- **Question density:** with nearly 2 questions per function, builders could cover more of each function than Gate 13's teams with under 1.
- Of the 68 edge calls that both N0 and Q got wrong, the examples fixed 0.51, against 0.91 in Gate 13. That is consistent with both explanations.

### 3. What it means for Hive

- On real rules, the combination of examples and questions is the strongest interface measured (78.0% against 49.6% in Gate 7), and examples break far less than questions.
- The examples' special value appears to need the owner to *choose* them, not just to confirm an agent's list. That points back to the open question from Gate 17: how to get a real owner to point.

## Honest odds

- Owner-chosen (not agent-drafted) examples on these rules would beat 19 questions by ≥ 1.3×: about 55%. This needs the owner's time; it is the cleanest next test on real rules.

## Limits

- One run per team; 10 functions, so the intervals are wide.
- The specs were rewritten for this gate. They are neutral and shared by all teams, but differ from Gate 7's, so the 49.6% comparison is across setups.
- Example inputs and hidden inputs come from one QA list (8% near copies).

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions and decision rules, pushed before the run |
| `referee/analyze.py` | Registered aggregate-only analysis |
| `results/summary.md`, `results/analysis.txt` | Arm-level numbers only |
