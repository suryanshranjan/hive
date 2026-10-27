# Gate 14 results: the decision tour, replicated, and contrast pairs, Oct 27 2026

**Question.** Gate 13's decision tour (one owner example per policy decision) lifted hidden correctness from 57.8% to 89.4% on one rule set. Does it replicate on a new rule-giver? And does pairing each decision with a contrast, a nearby input the decision does not cover, stop builders from stretching a rule?

**Answer.**
- **The tour replicated, more strongly.** 50 owner examples lifted hidden correctness from **42.4% to 95.6%** (+53.2 points, CI +42.8 to +63.2). Across two independent rule sets, a tour alone took builders to 89–96%.
- **Contrasts did not help; they hurt a little.** Tour plus contrasts reached 90.8%, 4.8 points *below* the tour alone (CI −11.4 to +0.6), and broke more calls (19 against 13). C2 and C3 failed, and the pre-registered rule fires: contrasts are dropped, and over-generalization is left to questions.
- **Why (conjecture):** a contrast placed next to a boundary invites builders to re-guess where the boundary is, and they sometimes guessed wrong (a slug cut moved, a rounding rule changed). The decision example alone, chosen by the owner, located the rule well enough.

## Setup

- **Rules.** A fresh independent rule-giver: Gate 13's brief plus `CONTRAST_EXAMPLES`, one per decision (`prompts/rulegiver_brief.md`). 1 to 4 declared decisions per function, five functions each. Not edited. Predictions and analysis code were pushed before the rules existed (commit 14d5ec9).
- **Teams** (3 builders each, no questions): **N0** (nothing); **T** (tour: 50 examples in 25 visible tests); **TC** (tour plus 50 contrasts: 50 visible tests).
- **Hidden suite.** 500 tests (seed 14200000), 70% edge calls, drawn only from TYPICAL and EDGE. Not committed.

| Team | Examples | Builder cost | Visible | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | 0 | $1.88 | 1,380/1,380 | **212/500 (42.4%)** | 33.0–53.2% | |
| T | 50 | $1.92 | 1,405/1,405 | **478/500 (95.6%)** | 90.6–99.8% | **+53.2** (CI +42.8 to +63.2) |
| TC | 100 | $2.35 | 1,430/1,430 | **454/500 (90.8%)** | 84.0–96.6% | +48.4 (CI +38.0 to +58.8) |

Rule-giver $1.05; total $7.19 at list price.

**Validity.** 1 of 149 hidden edge inputs is a strict near copy of a tour or contrast input: `age_band` contrast 18 against hidden 17.9. Only TC saw it, and T and TC scored the same on that function. No hidden input is near a tour example.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| C1 | T − N0 ≥ +20 points | **Held**: +53.2 |
| C2 | broken_TC ≤ 0.5 × broken_T | **Failed**: 19 against 13 (ratio 1.46) |
| C3 | TC hidden ≥ T hidden | **Failed**: −4.8 (CI −11.4 to +0.6) |
| C4 | T and TC pass all tour and contrast tests | **Held**: 25/25 and 50/50 |
| C5 | N0 below 70% | **Held**: 42.4% |
| Kill | T − N0 < +10 demotes the tour | **Did not fire** |
| Rule | C2 and C3 both fail: drop contrasts; over-generalization is left to questions | **Fired** |

## What it means

### 1. The decision tour is now established across two rule sets

| Gate | No tour | Tour | Tour plus 17 questions |
| --- | --- | --- | --- |
| 13 | 57.8% | 89.4% | 95.2% |
| 14 | 42.4% | 95.6% | (not run) |

The tour fixed 353 of N0's 362 edge errors here (0.98), against 0.76 in Gate 13. For comparison, the best builder-question team in any gate (Gate 12, 80 questions) fixed 0.76.

### 2. Contrasts move boundaries rather than pin them

Where TC did worse than T:

| Function | Decision | Tour example | Contrast | What TC then got wrong |
| --- | --- | --- | --- | --- |
| slugify_title | cut to at most 40 characters at a word boundary | a 56-character title | a 32-character title | cut a title of exactly 40 characters too early (10 calls), and cut long titles too short |
| meeting_slot | duration rounded up to a multiple of 15 | ('09:00', 50) | ('09:00', 45) | rounded start-relative times wrongly ('09:10', 20 gave 09:30 instead of 09:40) |
| initials | name particles skipped | 'Ludwig van Beethoven' | 'Ludwig Vann Beethoven' | returned '' for '' instead of NULL (11 calls): unrelated to the contrast, plausibly team churn |
| loyalty_tier | (both teams broke calls here) | | | 7 broken against T's 5 |

A contrast is a second data point near the boundary. Builders fit a new boundary between the two points, and the fit can land in the wrong place. One owner example, without a contrast, left the boundary where the builders' prior put it, which was mostly right.

### 3. Over-generalization is small at this level

T broke 13 calls that N0 had right, against 362 errors fixed: about 28 fixes per break. Gate 13 showed that questions on top of the tour repair what remains (95.2%).

## Design consequences for Hive's intent interface

1. **Step one: the owner's decision tour.** Established on two independent rule sets: 89.4% and 95.6% hidden, from 57.8% and 42.4%.
2. **Do not add contrasts.** Tested, and they hurt slightly (one run).
3. **Step two: builder questions** to repair the remainder (Gate 13: 95.2%).
4. **The crux is now the owner's side.** Every tour so far came from an agent that knew its own rules. Next: can a tour be produced from what a real owner actually has (written policy documents, past examples) when the owner cannot list their own decisions?

## Honest odds

- A tour from a self-aware owner keeps builders at or above 85% hidden on a third rule set: about 85%.
- A tour that a separate agent extracts from policy documents (no `DECISIONS` list) keeps at least half the tour's gain: about 55%. This is the real-world risk.

## Limits

- One run per team. TC − T has an interval reaching +0.6, so "contrasts hurt" is weak; "contrasts did not help" is the safer reading.
- The rule-giver wrote the tour, the contrasts and the hidden suite's EDGE list.
- The rule-giver is the same kind of model as the builders.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md`, `prompts/rulegiver_brief.md` | Predictions, decision rules and brief, pushed before the rules existed |
| `referee/analyze.py` | Registered analysis (committed before the run) |
| `referee/oracle.py` | Rules, declared decisions, tour and contrasts, unsealed after scoring (synthetic) |
| `results/` | Summary, analysis output, probes, cost per worker, run log, rule-giver output |
| `swarms/*.bundle`, `logs/` | All three teams' histories; worker logs |
