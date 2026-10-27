# Gate 5 results: asking about defaults first, on rules from an independent rule-giver, Oct 27 2026

**Question.** In Gate 4 both teams that could ask missed the same kind of rule: places where the owner departs from a convention the builders took for granted. Does a team told to ask about its defaults first (NULL, extreme values, invalid input) beat free asking? And does that hold for rules written by someone other than the experimenter?

**Answer: no.**
- Defaults-first scored 62.2% on the hidden tests and free asking 67.0%: a difference of −4.8 points, with a paired 95% interval of −14.6 to +4.2. The treatment was delivered: 37% of the defaults-first team's questions contained NULL, against 10% for the free team. So the registered kill condition fired: "ask about your defaults" does not carry over to another rule-giver.
- The gain from having 30 questions at all replicated a third time: +32.4 points.

## Setup

- **Rules.** An independent agent wrote all 20 rules from a neutral product-owner brief (`prompts/rulegiver_brief.md`). It had never seen this project's hypotheses, earlier rules or conversation. Its rules were checked only mechanically: they run, the types are right, repeated runs agree. They were not edited. The predictions, prompts and brief were pushed to GitHub before the rules existed (commit 5f1acd4).
- **Teams.** Three teams of 3 builders on the same engine as Gates 3 and 4, one run each. They differ only in one paragraph of the prompt (`prompts/ask_texts.md`):
  - **D0:** no questions.
  - **D30f:** 30 free questions; the control, with the same text as Gate 4's R30.
  - **D30d:** 30 questions, defaults first.
- **Hidden suite.** 500 tests (seed 5200000) drawn from the rule-giver's own typical and edge lists, 70% edge calls.

| Team | Questions | With NULL | Functions never asked | Tokens | Visible | Hidden tests | 95% CI by function | Edge calls right |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D0 | 0 | | 20 | 321k | 1,380/1,380 | **173/500 (34.6%)** | 26.6–44.0% | 54.4% |
| D30f | 30 | 3 (10%) | 2 | 348k | 1,380/1,380 | **335/500 (67.0%)** | 58.0–76.0% | 80.0% |
| D30d | 30 | 11 (37%) | 6 | 355k | 1,380/1,380 | **311/500 (62.2%)** | 48.6–74.6% | 75.0% |

All three teams got 100% of typical-case calls right. The replay of every commit and the call-by-call probe agree exactly. No team broke an existing test at any commit. The rule-giver used 137k tokens.

| Paired difference (bootstrapped over functions) | Points | 95% CI |
| --- | --- | --- |
| D30f − D0 | +32.4 | +20.8 to +44.0 |
| D30d − D0 | +27.6 | +14.2 to +41.4 |
| D30d − D30f | −4.8 | −14.6 to +4.2 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| H1 | All visible examples pass | **Held** |
| H2 | D30d ≥ D30f + 5 points | **Failed**: −4.8 points |
| H3 | D30f − D0 between +15 and +43 points | **Held**: +32.4 |
| H4 | Treatment delivered: ≥ 1/3 of D30d's questions contain NULL, < 1/5 of D30f's | **Held**: 37% and 10% |
| H5 | Rules not guessable: D0 below 70% | **Held**: 34.6% |
| Kill | D30d ≤ D30f while H4 holds | **Fired.** Asking about defaults does not carry over to another rule-giver. |

## Why defaults-first failed

1. **This rule-giver hid its policy elsewhere.** Only 7% of the no-questions team's errors involve NULL. My own rules in Gate 4 had put about a quarter of the remaining errors there. This rule-giver's surprises sit in the business logic instead. Builders reported, for example:
   - a 25% cap on invoice discounts;
   - a minimum late fee capped at 10% of the balance;
   - an 18% default tip when the tip is NULL;
   - a flat surcharge above 30 kg;
   - an unpaid 30-minute break on shifts over 6 hours;
   - billing dates moved off weekends;
   - an 'MINOR' age band.

   Where surprises sit depends on who writes the rules. The idea came from my own habits and does not carry over.
2. **Front-loading questions starved later functions.** The defaults-first team spent its budget on the functions claimed first: one builder asked 13 questions, 5 of them on shipping. It left 6 functions with no question at all, against 2 for the free team. Those 6 stayed near the no-questions level: shift_hours 36%, loyalty_tier 40%, late_fee 45%.
3. **Answers can mislead when a question changes two things at once.** The free team asked about `nps_score` with tiny groups of ratings that also contained NULL or out-of-range values, and got NULL each time. The builder concluded that any invalid rating voids the score. The real rule (checked in the oracle after scoring): invalid ratings are skipped, and fewer than 3 valid ratings give NULL. Every test group had 3 ratings including one invalid value, so only 2 valid ratings remained. That function fell from 77% (no questions) to 46%.

## Across Gates 3 to 5: what questions are worth

The 30-question teams, pooled over three rule sets (Gate 3: 1 team; Gate 4: 2; Gate 5: 2), give 100 team-function pairs. For each pair, the gain is the edge-call accuracy above the no-questions team's on that same function.

| Questions about that function | Mean gain in edge accuracy | Pairs |
| --- | --- | --- |
| 0 | −2.6 points | 14 |
| 1 | +19.5 points | 40 |
| 2 | +24.3 points | 27 |
| 3 | +33.9 points | 14 |
| 4 or more | +33.9 points | 5 |

This is observational, because builders chose what to ask about. But the pattern is steady: a function nobody asks about gains nothing, the first question is worth the most, and returns diminish after about three. Across rule sets, the gain of a 30-question team over no questions was +28.6, +29.0 and +32.4 points.

## What this changes

- **Replicated three times, including on an independent rule-giver's rules:** 30 questions add about 30 points of hidden correctness.
- **Not supported, twice:**
  - Gate 4: a strategy that plans the 30 questions by coverage.
  - Gate 5: a strategy that asks about defaults first.

  Neither beat free asking. How many answered questions reach each function shows up clearly in the data. No rule for choosing which questions to ask has yet shown an effect.
- **Practical rule for Hive's intent interface:** make sure every function gets at least one question before any function gets a third. The budget should spread across functions, not be spent first come, first served. In both Gate 4 and Gate 5, the unasked functions are where the swarm lost. This is a hypothesis built from the pooled data, not yet tested on its own.

## Limits

- One run per team.
- The pooled question-count table is observational.
- The rule-giver is the same kind of model as the builders. It is independent of my hypotheses, but not of the model's habits.

## Files

| Path | Contents |
| --- | --- |
| `prompts/` | Predictions, team prompt texts, the rule-giver's brief and the builder prompt, all pushed before the rules existed |
| `referee/oracle.py` | The independent rule-giver's 20 rules, unsealed after scoring |
| `referee/gen5.py`, `referee/probe.py` | Test generator and call-by-call scorer |
| `seed.bundle`, `swarms/` | Starting repo and the three teams' histories |
| `results/asks_*.log` | Every question and answer |
| `results/eval_*`, `results/probe_*`, `results/tokens.csv` | Per-commit replays, per-call scores, tokens |
