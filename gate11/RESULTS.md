# Gate 11 results: spread vs blocks of 3, stratified by headroom, Oct 27 2026

**Question.** Gate 8 proposed a law: each answered question fixes about half the edge errors still left on its function (p ≈ 0.55), so spreading questions beats blocks of 3. Run head to head, with the headroom imbalance that misled Gate 6 designed out, does spreading win, and does the law hold?

**Answer.**
- **Spreading won.** With the same 30 questions, the spread team fixed 1.25× the edge errors of the blocks team (197 against 157; 95% CI 1.00 to 1.78). P1 held.
- **But not for the law's reason. The law failed three of its four direct tests.** On these rules the curve was 0.08 / 0.25 / 0.65 / 0.63 of errors fixed at 0 / 1 / 2 / 3 questions: a weak first question, a strong second, and a **third worth nothing**. p came out 0.35 (CI 0.26 to 0.42), outside the registered 0.40 to 0.70.
- **What survives is narrower and better supported:** with a 30-question budget over 20 functions, giving each function 1 or 2 questions beat giving half of them 3 and the other half none. The geometric law with one constant p is withdrawn. The value of the first and third questions varies with the rule set.

## Setup

- **Rules.** A fresh independent rule-giver (same neutral brief as Gates 5, 6 and 8; $0.84) wrote 20 rules, checked mechanically (267 calls, deterministic) and not edited. Predictions and the power analysis were pushed before the rules existed (commit 20af7c5).
- **First attempt.** It stopped at a usage limit (HTTP 429) while the rule-giver was writing, before any rules or builders existed ($0.33). Per the lab rule, it was rerun from scratch with refreshed credentials. Log: `results/run_attempt1_usage_limit.log`.
- **Stage 1.** N0 (3 builders, no questions) ran alone and was scored. The 20 functions were sorted by N0's edge errors and paired with their neighbours; a coin (`random.Random(11000)`) picked each pair's "hi" function.
- **Stage 2.** Two teams of 3 builders, same prompt and ask text, 30 questions each, enforced per function:
  - **S:** 2 questions per hi function, 1 per lo function.
  - **B:** 3 per hi function, 0 per lo function.
- **Hidden suite.** 500 tests (seed 11200000), 70% edge calls. Not committed.

| Team | Questions | Builder cost | Minutes | Hidden tests | 95% CI by function |
| --- | --- | --- | --- | --- | --- |
| N0 | 0 | $2.14 | 2.5–3.0 | **183/500 (36.6%)** | 28.2–45.8% |
| S | 30 (as assigned) | $2.42 | 2.8–3.3 | **293/500 (58.6%)** | 48.2–69.4% |
| B | 30 (as assigned) | $2.71 | 2.8–4.2 | **278/500 (55.6%)** | 45.2–67.2% |

Paired differences: S − N0 **+22.0** points (CI +12.2 to +31.8); B − N0 **+19.0** (CI +7.6 to +31.8). Total cost $8.43 at list price.

## The measurement

Errors fixed = a function's edge calls right minus N0's. The two hi sets are the **same functions** in S and B, and so are the two lo sets. So the design measures the third question (S hi vs B hi) and the first question (S lo vs B lo) within the same functions.

| | Functions | N0 edge errors | S | B | Difference, same functions |
| --- | --- | --- | --- | --- | --- |
| hi | 10 | 219 | 2 questions: **0.65** | 3 questions: **0.63** | the 3rd question: **−0.01** (S fixed 3 more) |
| lo | 10 | 222 | 1 question: **0.25** | 0 questions: **0.08** (spillover) | the 1st question: **+0.17** |
| all | 20 | 441 | 197 fixed | 157 fixed | **R = 1.25** (CI 1.00 to 1.78) |

Per pair (`results/summary.json`; `referee/analyze.py` reproduces every number from the raw probes):

| Pair: hi / lo | N0 errors | S fixed | B fixed |
| --- | --- | --- | --- |
| panel_score / normalize_phone | 4 / 6 | +4 / −11 | +4 / −11 |
| split_bill / age_band | 11 / 12 | +11 / +4 | +11 / 0 |
| normalize_sku / money_format | 17 / 15 | +7 / +15 | +7 / 0 |
| vat_amount / net_price | 17 / 19 | +10 / +6 | +3 / +4 |
| credit_grade / shipping_cost | 20 / 20 | +7 / 0 | +4 / 0 |
| add_business_days / slugify_title | 21 / 22 | +15 / 0 | +21 / 0 |
| loyalty_points / business_days | 23 / 27 | +16 / +9 | +9 / **+18** |
| initials / fiscal_quarter | 32 / 31 | +16 / +6 | +16 / 0 |
| rating_stars / meeting_end | 33 / 32 | +23 / +14 | +23 / 0 |
| mask_card / late_fee | 41 / 38 | +33 / +12 | +41 / +7 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| P1 | Spread beats blocks: R ≥ 1.15 | **Held**: 1.25. The interval's lower end touches 1.00 |
| P2 | B's 3-question functions fix ≥ 0.75 of their errors | **Failed**: 0.63 |
| P3 | S's 1-question functions fix 0.35 to 0.75 | **Failed low**: 0.25 (0.17 above spillover) |
| P4 | Third estimate of p between 0.40 and 0.70 | **Failed**: 0.35 (CI 0.26 to 0.42) |
| P5 | ≥ 27 of 30 questions used in each arm | **Held**: 30 and 30 |
| P6 | N0 below 70% hidden | **Held**: 36.6% |
| Kill | R ≤ 1.0 restores blocks of 3 | **Did not fire** |
| Rule | P3 below 0.35 means Gate 6's weak first question was real, not only an imbalance | **Fired** |

## What it means

1. **One constant p does not describe the curve.** Share of edge errors fixed, by questions on the function:

   | Gate | 0 | 1 | 2 | 3 |
   | --- | --- | --- | --- | --- |
   | 6 | 0.15 | 0.51 | – | 0.92 |
   | 8 | 0.00 | 0.56 | 0.65 | 0.87 |
   | 11 | 0.08 | 0.25 | 0.65 | 0.63 |

   The second question lands at 0.65 in both gates that measured it. The first ranges from 0.25 to 0.56 and the third from 0.63 to 0.92, depending on the rule set. Gate 8's correction of Gate 6 still stands: Gate 6's 1-question group really did have half the headroom. But a weak first question can also be real (here, measured within the same functions).

2. **Conjecture: questions saturate at about the number of hidden decisions per function.** The rule-giver's brief demands at least two hidden policy decisions per function. Here two answers reached the ceiling and the third added nothing. In Gates 6 and 8 the third question still helped, so a ceiling below 1 (some errors sit where no question reaches) and the number of decisions both vary by rule set. Untested.

3. **Spillover is real but uneven, and it can be large.** B gave `business_days` no questions but fixed 18 of its 27 errors, plausibly because its neighbour `add_business_days` got 3 questions and the two share calendar code. Spillover on unasked functions ran 0.15, 0.00 and 0.08 across Gates 6, 8 and 11.

4. **Teams with no questions do not always guess the same.** `normalize_phone` lost 11 edge calls against N0 in both S and B, whether or not it was asked about. S and B agreed with each other, so N0 was the odd one. Gate 8's "the no-question guess is a fixed property of spec and model" is mostly but not always true. Part of every per-function gain is the baseline's own noise.

## Design consequences

- **Kept, with better evidence:** spread a fixed budget across functions rather than in blocks of 3. One head-to-head run: 1.25× (CI 1.00 to 1.78).
- **Refined:** aim for about 2 questions per function before any function gets a third. Here the third was worth nothing on the same functions; in Gate 8 it was worth more (different functions, so not a clean comparison).
- **Withdrawn:** the one-parameter law "each answer fixes about half of what is left" (Gate 8). It was a model fitted on two gates and failed on the third.
- **Kept:** stratify allowances by headroom and report shares of errors fixed. Without the matched pairs, the within-function third-question result would not have been measurable.

## Honest odds and what would kill this

- Spread beats blocks of 3 again on a new rule-giver: about 70% (one win, interval at 1.0).
- The 2nd question reaches about 0.65 on a new rule-giver, give or take 0.1: about 50%. Two gates agree, but the shape varies.
- **Kill for "2 before a 3rd":** a within-function test where the third question adds ≥ 0.15 of errors fixed.

**Cheapest next experiment.** Repeat this exact design on a new rule-giver ($8.4, about 12 minutes), with one change registered first: count each function's hidden decisions in the oracle after scoring, and test whether questions-to-saturation tracks that count.

## Limits

- One run per team; 10 pairs. The ratio's interval reaches 1.0.
- N0 is used both to form pairs and as the baseline. That affects S and B alike, but N0's own guessing noise (point 4) enters every share.
- The rule-giver is the same kind of model as the builders.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions, decision rules and pre-flight power, pushed before the rules existed |
| `referee/power.py`, `referee/analyze.py` | Pre-flight Monte Carlo; independent recomputation from raw probes |
| `referee/oracle.py` | The rule-giver's 20 rules, unsealed after scoring (synthetic) |
| `results/summary.md`, `results/summary.json` | `run_gate.py` output, including pairs and ratio |
| `results/pairs.json`, `results/allowance_*.json`, `results/asks_*.log` | Pairing, allowances, every question and answer |
| `results/probe_*.json.gz`, `results/tokens.csv`, `results/run*.log`, `results/rulegiver.json` | Probes, cost per worker, run logs (both attempts), rule-giver output |
| `swarms/*.bundle`, `logs/` | All three teams' histories; worker logs |
