# Gate 12 predictions, registered before the rules exist (Oct 27 2026)

**Question.** The question curve changes shape from one rule set to the next. Gate 11's third question was worth nothing; Gates 6 and 8's third question still helped. The conjecture from Gate 11: **questions saturate near the number of hidden policy decisions a function carries.** If so, the right allocation is "about one question per hidden decision", and a builder's estimate of a function's decisions is the thing worth predicting.

**Design (one command: `python3 lab/run_gate.py lab/experiments/g12_saturation.json`).**
- **Rules.** A fresh independent rule-giver gets Gate 5's brief with one change (`gates/gate12/prompts/rulegiver_brief.md`): exactly 5 functions carry 1 hidden decision, 5 carry 2, 5 carry 3 and 5 carry 4. It declares them in a private `DECISIONS` dict, sealed until scoring. `run_gate.py` checks the counts mechanically and edits nothing.
- **Teams.** Four teams of 3 builders, same prompt and ask text: **N0** (no questions), **Q1**, **Q2** and **Q4** (1, 2 or 4 questions on *every* function: 20, 40 and 80 questions). Each function's curve is measured at 0, 1, 2 and 4 questions on the same function.
- **Hidden suite.** 25 tests per function (seed 12200000), 70% edge calls.
- **Analysis.** Registered as code: `gates/gate12/referee/analyze.py`, committed with this file. share_q = (edge calls right in Qq − right in N0) / N0's edge errors, for functions with at least 5 N0 edge errors.

**Pre-flight power** (`gates/gate12/referee/power.py`, 20,000 runs; per-function noise from Gates 6, 8 and 11). H1: share = 0.75 · min(1, q/d). H0: the same average curve for every d.

| | P(D1 holds) | P(D2 holds) | P(ρ ≤ 0) |
| --- | --- | --- | --- |
| H1, saturation tracks decisions | 0.82 | 0.72 | 0.03 |
| H0, shape independent of decisions | 0.18 | 0.10 | 0.51 |

| # | Prediction |
| --- | --- |
| D1 | The first question does more where there are few decisions: mean share_1 over d ∈ {1,2} minus over d ∈ {3,4} ≥ +0.15 |
| D2 | Saturation tracks decisions: Spearman ρ(d, q*) ≥ 0.3, where q* is the smallest q ∈ {1,2,4} reaching 0.8 of the function's best share |
| D3 | The pooled curve rises: share at Q1 ≤ Q2 ≤ Q4 |
| D4 | Enough questions reach the ceiling: pooled share at Q4 ≥ 0.80 |
| D5 | Treatment delivered: at least 18 / 36 / 72 of the 20 / 40 / 80 allowed questions used in Q1 / Q2 / Q4 |
| D6 | Rules not guessable: N0 below 70% hidden |

Kills and decision rules:
- **D1 ≤ 0 and ρ ≤ 0:** the decision-saturation conjecture is dead. The curve's shape is set by something other than the number of hidden decisions.
- **D1 and D2 both hold:** adopt "about one question per expected hidden decision" as the allocation rule, and make estimating a function's decisions the next problem.
- **D4 fails:** some errors sit where no question reaches; measure that ceiling directly next.

**Validity check, reported whatever the outcome.** The declared decisions are the rule-giver's own count. After scoring, the EDGE list is checked to cover each declared decision, and any function whose rule visibly has more or fewer choices than declared is listed (not dropped).

**Honest prior.** About 45% that D1 and D2 both hold.

**Cost.** About $11 at list price (rule-giver about $0.9; 12 builders); about 10 minutes.
