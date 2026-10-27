# Gate 6 results: what each question is worth, measured by random assignment, Oct 27 2026

**Question.** Gates 3 to 5 showed that functions which got more questions came out more correct. But builders chose what to ask, so that pattern could be selection rather than cause. Do questions cause the gain? And what is the shape of the curve: is the first question worth the most?

**Answer.**
- **Questions cause the gain.** Functions randomly allowed 3 questions gained +36 points of edge-case accuracy more than functions allowed none (95% CI +20 to +51).
- **The first question is *not* worth the most.** One question bought +12 points, barely above the +8 for none. Three bought +44. The observational table (first question about +20) was misleading, and the "spread the budget" rule I proposed after Gate 5 would have been the worst allocation of all.

## Why this design (Wright check before flying)

The test proposed after Gate 5 ("one question per function before any gets a third") was fed through our own table first. It predicted an advantage of 0 to 1 point over free asking, against about ±10 points of single-run noise, so that test could not have told us anything. Instead, the number of questions per function was **randomly assigned**, which turns the observational pattern into an experiment.

## Setup

- **Rules.** A new independent rule-giver agent wrote 20 rules (same neutral brief as Gate 5). They were checked mechanically only, not edited. Predictions and the assignment procedure were pushed to GitHub before the rules existed (commit 43d998f).
- **Teams.** Three teams of 3 builders, one run each:
  - **N0:** no questions.
  - **N30f:** 30 free questions, the control.
  - **NQ:** each function has a fixed allowance of 0, 1 or 3 questions, enforced by the product-owner server.
- **Assignment.** The pre-registered shuffle (`random.Random(6000)`) gave 6 functions 0 questions, 7 functions 1, and 7 functions 3: 28 in all. NQ used all 28, exactly as allotted.
- **Hidden suite.** 500 tests (seed 6200000), 70% edge calls, from the rule-giver's own lists.

| Team | Questions | Tokens | Visible | Hidden tests | 95% CI by function | Edge calls right |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | 0 | 327k | 1,380/1,380 | **204/500 (40.8%)** | 30.6–51.4% | 59.9% |
| N30f | 30 (3 functions never asked) | 357k | 1,380/1,380 | **329/500 (65.8%)** | 54.2–77.0% | 79.5% |
| NQ | 28 (as assigned) | 355k | 1,380/1,380 | **352/500 (70.4%)** | 57.4–82.0% | 80.7% |

The replays of every commit and the call-by-call probes agree exactly, and no team broke an existing test. The rule-giver used 132k tokens.

## The measurement

For each function, the gain is NQ's edge-call accuracy minus N0's on that same function.

| Allowance (random) | Functions | Mean gain | 95% CI (bootstrap over functions) |
| --- | --- | --- | --- |
| 0 questions | 6 | **+7.9** | −1.3 to +17.7 |
| 1 question | 7 | **+11.9** | +7.0 to +16.5 |
| 3 questions | 7 | **+44.0** | +31.0 to +55.6 |
| 3 minus 0 | | **+36.1** | +19.7 to +51.2 |

Gain(1) / gain(3) = 0.27.

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| K1 | All visible examples pass | **Held** |
| K2 | Gain(3) − gain(0) ≥ 15 points, and gain(0) < +8 | **Held**: +36.1, and +7.9 (just under) |
| K3 | The first question is worth the most: gain(1) ≥ half of gain(3) | **Failed**: 0.27 |
| K4 | Fourth replication: N30f − N0 between +15 and +43 | **Held**: +25.0 (CI +13.8 to +36.6) |
| K5 | Rules not guessable: N0 below 70% | **Held**: 40.8% |
| K6 | At least 25 of 28 allowed questions used | **Held**: 28 of 28 |
| Kill (K2) | Gain(3) − gain(0) < +5 would mean selection, not cause | **Did not fire**: questions cause the gain |
| Kill (K3) | If K3 fails, concentrating questions beats spreading them | **Fired** |

## What it means

1. **Intent arrives as rules, and a rule needs several answered points to pin down.** Each of these rule-giver's functions hides at least two policy decisions. One answer usually shows only that something is odd, and builders then guess the wrong rule. Two clear cases:
   - One NQ builder, with a single question about `fiscal_quarter`, saw that a late-March timestamp falls into the next fiscal year. It concluded the rule was a time-zone shift. The real rule (checked in the oracle after scoring): any date from 28 March counts as the next year's first quarter. The rule does not depend on time zone.
   - With 3 questions, builders could vary one thing at a time and triangulate. `median_price` (3 questions) went from 35% to 100%.

   Gate 4's lesson, "an answer pins a point, not a rule", is the mechanism behind the curve.
2. **The observational table misled.** Pooled over Gates 3 to 5, functions with 1 question gained about +20. Builders chose to stop at one question where one sufficed; random assignment removes that choice. The free team in this gate shows a pattern closer to the randomized one (+5, +14, +19, +36 at 0, 1, 2, 3 questions).
3. **Some knowledge spreads across functions.** Functions allowed no questions still gained +7.9 (CI −1.3 to +17.7). The largest gains were in money functions next to ones that were asked about (`overtime_pay` +22, `prorated_refund` +25), plausibly through shared conventions such as rounding. This is a conjecture.
4. **The allocation follows by calculation (model).** The curve was measured at 0, 1 and 3, so gain(2) is interpolated; treat these numbers as a model. Mean edge gain for 30 questions:

| Allocation | Model mean edge gain |
| --- | --- |
| Spread: one each plus 10 second questions | 19.9 points |
| Free teams (Gates 5, 6) | 21.9 to 24.1 points |
| Concentrate: 3 each on 10 functions | **25.9 points** |

   The spread rule proposed after Gate 5 would have done worse than free asking. NQ, a randomized mix, beat free asking by +4.6 points (CI −5.8 to +16.0), consistent with the model but within noise.

## Design consequence for Hive's intent interface

- Spend questions in blocks of about 3 per function, enough to triangulate a rule. Don't sprinkle one per function.
- Vary one thing per question (Gate 5).
- Write answers as tests (Gate 4).
- Still open: *which* functions should get the blocks. With a fixed budget, some functions will get none. They will be about as wrong as if nobody had asked, apart from whatever spills over from related functions.

## Limits

- One run per team; 6 to 7 functions per allowance group, so the intervals are wide.
- Gain(2) was not measured.
- The curve was measured on one rule-giver whose brief demanded at least two hidden decisions per function. Functions with a single quirk may well show a steeper first question, as my own Gate 3 and 4 rules seemed to.
- The rule-giver is the same kind of model as the builders.

## Files

| Path | Contents |
| --- | --- |
| `prompts/` | Predictions, assignment procedure, team prompts and rule-giver brief, pushed before the rules existed |
| `referee/oracle.py` | The rule-giver's 20 rules, unsealed after scoring |
| `referee/gen6.py`, `referee/probe.py`, `referee/ask_server_quota.py` | Test generator, call-by-call scorer, allowance-enforcing product owner |
| `results/allowance.json` | The random assignment |
| `results/analysis.json` | Per-function gains and questions |
| `results/asks_*.log` | Every question and answer |
| `seed.bundle`, `swarms/`, `results/eval_*`, `results/probe_*`, `results/tokens.csv` | Starting repo, histories, replays, probes, tokens |
