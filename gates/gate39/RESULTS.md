# Gate 39 results: a wind tunnel for Hive's interview, Oct 29 2026

**Question.** With a perfect owner, someone who holds the exact rules and never contradicts himself, how much of the owner's intent does Hive's interview (as shipped) get into the code? And where does the rest leak: in what Hive asks, in how it writes his answers down, or in the builders?

**Answer.**
- **The builders are not the leak.** Given the owner's complete rule sheet in prose (R), three builders passed **250 of 250** hidden tests. They fixed all 217 of N0's edge errors and broke none.
- **Hive's interview reached 76.0%** (H), the same as the owner's decision tour (T, 75.6%). That is 24 points below the complete sheet.
- **Where the 24 points leak, per decision:** 8 of the 25 decisions were **never asked**. All 8 are about what the product shows for unusual input (an unreadable date, letter case, separators, leftover fractions); Hive's planner is told to skip "technical choices". 4 of the 17 asked decisions were **lost between his answers and the sheet**: 1 by a Hive bug ("mostly right, but…" replaced his whole rule), 2 by a defect in this test's harness, and 1 written only in part. 13 reached the sheet right.
- **Examples lost to complete prose here:** the decision tour fixed 0.85 of N0's errors and broke 20 correct calls. The complete sheet fixed 1.00 and broke none.
- **Fixed in Hive now:** a correction amends the rule it answers instead of replacing it; the terminal restates a rule before asking for its correction; an answer in his own words keeps any detail the nearest choice lacks. **Next:** Gate 40 tests asking about unusual input too.

## Setup

- **Rules.** A fresh independent rule-giver: 10 functions (9 scalar, 1 aggregate), 25 declared decisions (2 functions with 1, 3 with 2, 3 with 3, 2 with 4), checked deterministic. Not edited. Predictions, briefs, the pre-launch step and the analysis were pushed before the rules existed (`8e73fb2`).
- **Suites.** 2 visible typical examples per function (seed 39100). Hidden: 250 tests, 25 per function, 70% edge calls (seed 39200000). The hidden suite is not committed.
- **Synthetic owner.** One headless Claude Code call per prompt, holding the rules as `oracle.py` and allowed to run them. It sees the screen a terminal user would see and types a letter, a sentence, or Enter.
- **Teams.** 3 builders each, no questions:
  - **N0:** spec and examples.
  - **H:** plus the rules from `hive.interview.interview()` exactly as `hive start` runs it in a terminal: 19 situations, 24 owner replies, 10 confirmed rules, in Hive's own wording for builders.
  - **R:** plus the owner's complete rule sheet: 70 rules, written from the oracle by a documenter.
  - **T:** plus the owner's decision tour: one example per decision, 25 examples in 12 visible tests.
- **Judge.** Ran before any build existed. It labelled each decision: was it asked, and is it stated right, partly, wrong or absent in H and in R.
- **Model.** In this session `claude -p` ran builders on Sonnet 5.5 (with Haiku), not the model of earlier gates. Builders finished in 0.2 to 2.2 minutes each. Compare teams within this gate only.

| Team | Gets | Builder cost | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- |
| N0 | nothing | $0.57 | **96/250 (38.4%)** | 23.2–54.0% | |
| H | Hive's interview (10 rules) | $0.62 | **190/250 (76.0%)** | 57.2–92.0% | +37.6 (CI +19.2 to +57.2) |
| R | complete rule sheet (70 rules) | $0.54 | **250/250 (100%)** | 100–100% | +61.6 (CI +45.2 to +76.8) |
| T | decision tour (25 examples) | $0.55 | **189/250 (75.6%)** | 65.6–84.4% | +37.2 (CI +23.6 to +50.8) |

Share of N0's 217 wrong edge calls fixed: **H 0.65** (141), **R 1.00** (217), **T 0.85** (184). Correct N0 edge calls broken: H 2, R 0, T 20 (of 221).

Other costs: rule-giver $0.41, documenter $0.17, synthetic owner $1.65 (24 calls), judge $0.20. Hive's own model calls during the interview were not metered. Total about $4.70 plus those calls.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| W1 | T fixes ≥ 0.85 of N0's edge errors | **Failed by a hair:** 184/217 = 0.848 |
| W2 | R ≥ T − 5 points | **Held:** R − T = +24.4 |
| W3 | 0.40 ≤ K ≤ 0.80 | **Failed:** K = (H − N0)/(T − N0) = 1.01 (CI 0.53 to 1.60) |
| W4 | Interview asks about 50–85% of decisions, and H states ≥ 80% of those right | **Failed:** asked 17/25 (0.68, in range); stated right 13/17 (0.76) |
| W5 | N0 below 65% | **Held:** 38.4% |
| Kill | K < 0.25 | **Did not fire** |
| Rule | K ≥ 0.85 → "the interview is not the leak with a consistent owner" | **Fired by its letter; withdrawn.** Its premise, that the tour is the ceiling, failed: the complete sheet reached 100% and the tour only 75.6%. Against the real ceiling the interview leaks 24 points, and the judge's labels show where. |
| Rule | Coverage < 0.6 with transfer ≥ 0.8 / transfer < 0.7 / R < T − 10 | **None fired** (coverage 0.68, transfer 0.76, R above T) |

## What it means

### 1. A complete rule sheet is executed perfectly

250 of 250 hidden tests passed, with 0 calls broken, from 70 plain-words rules and no examples. This sheet was written from the code by an agent that could run it. It states every decision, plus how each function treats NULL, empty text and numbers given as text. No real owner writes that much. But it settles what the builders can do: **every point lost in this gate is a rule that never reached them, not a rule they failed to follow.** Where H's sheet stated all of a function's decisions right (4 functions), H's builders fixed 0.92 of N0's errors there, against 0.51 elsewhere.

### 2. Where the interview leaked

| Fate of the 25 decisions | Count | Which, and why |
| --- | --- | --- |
| Never asked | 8 | `fiscal_quarter`: an invalid date gives `n/a`, a date before 2000 gives `legacy`, an integer YYYYMMDD is accepted. `biz_days_add`: n = 0 rolls forward to a business day; an invalid date gives empty text. `ship_cost`: the zone letter ignores case. `mask_card`: spaces and dashes are stripped. `late_fee`: fractional cents round up. **All are about unusual input or leftover fractions.** Hive's planner is told to list "business outcomes, not technical choices", yet each one is what the receipt or report shows. |
| Asked, lost on the way to the sheet | 3 | **`late_fee` cap (Hive bug).** He was shown the reading "2% per month or part-month, 5-day grace, capped at ₹50" and replied "Mostly right, but you left out a minimum: …". Hive took his correction as the whole rule, so the rate and the cap he had just confirmed were lost. **`loyalty_tier`, 2 decisions (harness defect).** The general rule was right on the threshold but had lost the `void` label. He marked it wrong. When asked "Rule 2: what should it be?", the harness had cleared his screen, so the owner no longer saw rule 2 and wrote an unrelated (correct) rule in its place. A terminal user would still see the sheet above the prompt. The phone restates the rule; the terminal prompt did not. The `void` label itself had been dropped earlier: Hive mapped his own words ("no level… marked void") to the nearest choice ("no level at all"). |
| Asked, stated in part | 1 | `mask_card`: INVALID for "3 digits or a letter", but not the 12–19 digit range |
| Asked and stated right | 13 | |

Two questions (`late_fee` limits, `loyalty_tier` at exactly 5,000 points) were skipped because an earlier answer "settled" them. Both skips were sound: the cap was in his earlier fee answer, and the 5,000-point threshold still reached the sheet he was shown (rule 2, before the harness defect replaced it).

### 3. Examples generalize less than words

The tour gave one example per decision and fixed 0.85, while breaking 20 calls that N0 had right: builders stretched the examples. Gates 13–15 found the tour beating a partial handbook. Here a *complete* sheet beat the tour by 24 points. Gate 15 had already seen this on the functions its handbook covered fully (1.00 both ways). **Model:** what fixes errors is the share of decisions that reach the builders, stated whole. Examples are a way to state a decision; full sentences are a better one when they exist.

## Turned into the product (this commit)

- **A correction amends; it does not replace** (`hive/interview.py`, `_amend`). "Mostly right, but…" to a reading, or a correction to a rule on the sheet, now keeps every part of the rule he did not object to.
- **The terminal restates the rule** before asking what it should be, as the phone already did.
- **His own words keep their detail** (`hive/explain.py`, `UNDERSTAND`). An answer counts as a choice only when it adds nothing the choice lacks: no label, amount, limit or exception.
- All 203 checks pass; the two tests of corrections now check that the shown rule is kept.
- **Not yet changed:** the planner still skips unusual input. Gate 40 tests asking about it before it ships.

## Honest odds

- A complete rule sheet reaches ≥ 95% again on fresh rules (Gate 40 replicates it): about 75%.
- Asking about unusual input raises coverage above 85% and adds ≥ 8 points: about 50%. The cost is more questions for the owner.

## Limits

- One run per team, one rule set, 10 functions. The H − T tie and K = 1.01 have wide intervals.
- The owner is synthetic: perfectly consistent, never tired, and able to run his rules. This is the machine's ceiling, not a person's result (Gates 36–38 measure the person).
- The harness defect cost H the 2 `loyalty_tier` decisions (14 of N0's edge errors; H fixed 0 of them). Leaving that function out, H is 78.2%, T 76.0%, R 100%. Gate 40's harness keeps the whole terminal history.
- The complete sheet was written from the code and is richer than any owner's. It is a ceiling, not a channel.
- Rule-giver, owner, documenter, judge and builders are the same family of models. The builders ran on a different, faster model than in earlier gates.

## Files

| Path | Contents |
| --- | --- |
| `prompts/` | Predictions; briefs for the rule-giver, owner, documenter and judge; builder prompt (pushed before the rules existed) |
| `referee/wind_tunnel.py`, `referee/analyze.py` | The pre-launch step (documenter, interview, judge, ask texts) and the registered analysis |
| `referee/oracle.py` | The rules, unsealed after scoring (synthetic) |
| `results/` | Summary, analysis, probes, worker costs, run log, ask texts, the interview's questions, drafts, sheet and full transcript, judge labels (`wind_tunnel.json`) |
| `swarms/*.bundle`, `logs/` | All four teams' histories; worker logs |
