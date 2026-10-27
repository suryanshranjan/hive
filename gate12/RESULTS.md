# Gate 12 results: does question saturation track hidden decisions? Oct 27 2026

**Question.** Gate 11 suggested that questions stop helping at about the number of hidden policy decisions a function carries. Here the rule-giver set that number (1 to 4, five functions each) and declared it privately, and four teams asked 0, 1, 2 or 4 questions on *every* function. So each function's curve is measured on itself.

**Answer.**
- **Decisions predict how much a question does, but not when questions stop helping.** One question fixed 0.69 of the errors on functions with 1 or 2 decisions, against 0.39 on functions with 3 or 4 (D1 held, +0.30). But the point where a function stopped improving barely tracked its decisions (ρ = +0.18; D2 failed).
- **The reason is a floor that more questions do not lower.** 21% of the no-question team's edge errors were never fixed by any team, even with 4 questions per function. 87% of the errors left after 4 questions were also left after 1 and after 2.
- **Every stuck error we inspected is a declared decision that no question ever probed:** integer dates, a leading "00" in phone numbers, a "75+" age band, a 40-character slug cap, holidays, a 5,000-point cap. Builders kept asking about what they could imagine; extra questions went to more of the same region.
- **Discovery: the bottleneck is where questions point, not how many there are.** Builders cannot ask about a decision they cannot imagine. Design change: the person who knows where the decisions are (the product owner) should point at them. Gate 13 tests that.

## Setup

- **Rules.** A fresh independent rule-giver with one brief change (`prompts/rulegiver_brief.md`): exactly 5 functions with 1, 2, 3 and 4 hidden decisions, declared in a private `DECISIONS` dict. Checked mechanically (254 calls, deterministic; counts 1:5, 2:5, 3:5, 4:5) and not edited. Predictions, power analysis and the analysis code were pushed before the rules existed (commit 23cbe83).
- **Teams.** Four teams of 3 builders, same prompt and ask text: N0 (no questions), Q1, Q2 and Q4 (1, 2 or 4 questions allowed on every function).
- **Hidden suite.** 500 tests (seed 12200000), 70% edge calls. Not committed.

| Team | Questions used | Builder cost | Minutes | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | 0 | $2.06 | 2.3–3.1 | **184/500 (36.8%)** | 27.2–47.6% | |
| Q1 | 20 of 20 | $2.42 | 2.6–2.8 | **341/500 (68.2%)** | 58.2–77.6% | +31.4 (CI +20.0 to +42.8) |
| Q2 | 39 of 40 | $2.34 | 2.2–2.7 | **375/500 (75.0%)** | 65.2–85.2% | +38.2 (CI +27.4 to +49.6) |
| Q4 | 78 of 80 | $2.56 | 2.9–3.6 | **408/500 (81.6%)** | 72.8–90.0% | +44.8 (CI +34.0 to +55.4) |

Rule-giver $0.91; total $10.29 at list price.

## The measurement (registered code: `referee/analyze.py`)

Share of N0's edge errors fixed, for the 19 functions with at least 5 N0 edge errors (`percent_change` had none):

| Declared decisions | Functions | 1 question | 2 questions | 4 questions |
| --- | --- | --- | --- | --- |
| 1 | 4 | 0.69 | 0.86 | 1.00 |
| 2 | 5 | 0.68 | 0.75 | 0.79 |
| 3 | 5 | 0.46 | 0.55 | 0.66 |
| 4 | 5 | 0.32 | 0.40 | 0.64 |
| pooled | 19 | **0.57** | **0.67** | **0.76** |

More decisions mean a slower rise *and* a lower level after 4 questions. Per function (d, N0 errors, share at 1 / 2 / 4):

| Function | d | E | 1 / 2 / 4 | Function | d | E | 1 / 2 / 4 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| grade_letter | 1 | 13 | 0.31 / 1.00 / 1.00 | age_band | 3 | 14 | 0.43 / 0.43 / 0.43 |
| initials | 1 | 28 | 1.00 / 1.00 / 1.00 | business_days_add | 3 | 35 | 0.66 / 0.66 / 0.66 |
| invoice_no | 1 | 22 | 1.00 / 1.00 / 1.00 | net_price | 3 | 30 | 0.53 / 1.00 / 0.53 |
| tier_discount | 1 | 22 | 0.45 / 0.45 / 1.00 | slugify_title | 3 | 30 | 0.67 / 0.67 / 0.67 |
| fiscal_quarter | 2 | 12 | 0.42 / 0.42 / 0.42 | star_rating | 3 | 5 | 0.00 / 0.00 / 1.00 |
| mask_card | 2 | 18 | 0.61 / 1.00 / 1.00 | avg_rating | 4 | 15 | 0.33 / 0.40 / 0.40 |
| minutes_to_hhmm | 2 | 30 | 0.83 / 0.83 / 1.00 | late_fee | 4 | 33 | 0.15 / 0.30 / 1.00 |
| phone_digits | 2 | 27 | 0.52 / 0.52 / 0.52 | loyalty_points | 4 | 27 | 0.85 / 0.85 / 0.85 |
| split_bill | 2 | 27 | 1.00 / 1.00 / 1.00 | shipping_cost | 4 | 33 | 0.24 / 0.45 / 0.45 |
| | | | | sku_check | 4 | 20 | 0.00 / 0.00 / 0.50 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| D1 | Share at 1 question, d ∈ {1,2} minus d ∈ {3,4} ≥ +0.15 | **Held**: +0.30 (9 vs 10 functions) |
| D2 | Spearman ρ(d, q*) ≥ 0.3 | **Failed**: +0.18 |
| D3 | Pooled share rises Q1 ≤ Q2 ≤ Q4 | **Held**: 0.57, 0.67, 0.76 |
| D4 | Pooled share at Q4 ≥ 0.80 | **Failed**: 0.76 |
| D5 | ≥ 18 / 36 / 72 questions used | **Held**: 20, 39, 78 |
| D6 | N0 below 70% hidden | **Held**: 36.8% |
| Kill | D1 ≤ 0 and ρ ≤ 0 | **Did not fire** |
| Rule | D4 fails: some errors sit where no question reaches; measure that ceiling next | **Fired** |

Pre-flight power, for the record: under "saturation tracks decisions", D1 held 82% of the time and D2 72%. One of the two held, which is consistent with a real but partial effect.

## What it means

### 1. Decisions set the slope; a floor of unprobed decisions sets the ceiling

D2 failed because q* is dominated by plateaus. Six functions show the same share at 1, 2 and 4 questions. A plateau gives q* = 1 whatever d is, which flattens ρ. Plateaus are not saturation: the function stops improving with errors still left.

`referee/targeting.py` (post hoc):
- N0 made 412 edge errors. **85 (21%) were still wrong in Q1, Q2 and Q4 alike.**
- Of the 98 errors left after 4 questions per function, **87% were also left after 1 and after 2.**

Each stuck error inspected matches one of the rule-giver's declared decisions, which also checks that the declared labels were honest:

| Function | Declared decision never probed | What the 4 questions on it probed instead |
| --- | --- | --- |
| fiscal_quarter | integer YYYYMMDD accepted | time parts, NULL, '', 'garbage', bad and malformed dates |
| phone_digits | leading 00 converted to + | +, parentheses, extensions, letters, '', NULL, numbers |
| age_band | 75 and over gives 75+ | minors, 18th birthdays, Feb 29, NULL, future dates |
| slugify_title | max 40 characters, cut at a word | accents, apostrophes, &, underscores, NULL, '!!!' |
| business_days_add | Jan 1 and Dec 25 skipped | weekends, negative n, NULL, non-numeric n |
| loyalty_points | capped at 5,000 per purchase | case, unknown tiers, negatives, fractions, '' |

**Correction to my first reading.** I first read this as builders wasting questions on NULL and garbage. They don't much: only 10% to 16% of asked values were generic invalid inputs. The questions were reasonable QA cases. They covered the region a careful engineer imagines, and the stuck decisions lay outside it: extreme magnitudes (caps, 75+, 40 characters), alternative input formats (integer dates, "00"), and calendar facts (holidays).

### 2. A model for the curve (conjecture)

For a function with d decisions, of which u lie outside what builders think to probe:

```
share fixed(q) ≈ (1 − u/d) · (1 − (1 − r)^q)
```

r is how fast questions cover the imaginable decisions; u/d is the floor. Pooled here, the floor is about 0.21 and the imaginable part is mostly covered by 2 to 4 questions. This reconciles Gates 6, 8 and 11. Rule sets differ in how many decisions sit outside builders' imagination, so their curves top out at different heights (Gate 11's 0.63, Gate 6's 0.92). One constant p could not fit that. This is a conjecture, written after the data.

### 3. More questions are a weak lever; who chooses the points is the strong one

Going from 40 to 80 questions bought +6.6 points of hidden pass. The 85 stuck errors need someone who knows where the decisions are. That is the product owner, who wrote them.

## Design consequences

- **New default for the intent interface (conjecture, to be tested in Gate 13):** the product owner volunteers a *decision tour*, one worked example per policy decision, given as tests. Builder questions then fill in around it.
- **Builder questions:** keep spreading them (Gate 11), but expect a floor. Prompt builders explicitly to probe magnitudes, alternative formats and calendar or domain facts. Gate 5's "defaults first" did not help, so this is a guess until tested.
- **For experiments:** report the unreached floor (errors no team fixes) as well as gains.

## Honest odds

- A decision tour of equal size (one example per decision, about 50 answered values) fixes more errors than about 50 builder-chosen answered values: about 75%.
- A tour plus builder questions passes the 0.80 ceiling that questions alone missed: about 60%.

## Limits

- One run per team. The per-function curves use three different teams, so each comparison includes team-to-team noise (Gate 11's `normalize_phone`).
- The decision counts are the rule-giver's own. The stuck errors matched its labels, but a function may hide more or fewer choices than declared.
- The targeting analysis and the floor model came after the data. They are conjectures until Gate 13 tests them.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md`, `prompts/rulegiver_brief.md` | Predictions, decision rules, power, and the brief variant, pushed before the rules existed |
| `referee/analyze.py` | Registered analysis (committed before the run) |
| `referee/power.py`, `referee/targeting.py` | Pre-flight power; post-hoc targeting and floor analysis |
| `referee/oracle.py` | The rules and declared decisions, unsealed after scoring (synthetic) |
| `results/` | Summary, allowances, every question and answer, probes, cost per worker, run log, rule-giver output |
| `swarms/*.bundle`, `logs/` | All four teams' histories; worker logs |
