# Gate 15 results: a decision tour from a policy handbook, Oct 27 2026

**Question.** The decision tour works when the owner can list their own decisions (Gates 13, 14). A real owner has a handbook that states some decisions clearly, some vaguely and leaves some out. Can an extractor agent turn that handbook into a tour (choosing the inputs, with the owner answering them)? And is that better than handing builders the handbook?

**Answer.**
- **Yes: the extracted tour keeps three quarters of the owner's tour gain.** Hidden correctness: no help 44.6%, handbook 77.2%, **extracted tour 80.6%**, owner's own tour 92.6%. X1, X2, X3, X4 and X6 held; X5 failed on a technicality (below).
- **Omitted decisions are the floor that remains.** On functions where the handbook left nothing out, both handbook paths fixed every N0 edge error (1.00). On functions with at least one omitted decision, the handbook fixed 0.60 and the extracted tour 0.70.
- **The extractor sometimes recovers what the handbook omits.** On `phone_format`, whose second decision is missing from the handbook, the extracted tour fixed 31 of 31 errors and the handbook team 0.
- **Design consequence:** the practical first step of Hive's intent interface is *documents → extractor picks examples → owner answers them → tests*. The owner's own decision list remains better by 12 points (CI −0.4 to +23.6), mostly on decisions nobody wrote down.

## Setup

- **Rules.** A fresh independent rule-giver: Gate 13's brief plus a prose `HANDBOOK` (1,238 words, organised by topic) and a private `HANDBOOK_STATUS`. Of the 50 decisions, 20 were clear, 15 vague and 15 omitted, exactly as required. The handbook quotes no TYPICAL or EDGE input. Not edited. Predictions and analysis code were pushed before the rules existed (commit c04ed1c).
- **Extractor.** A separate headless agent saw only the handbook and the one-line spec ($0.26) and picked 50 inputs. **14 were exact TYPICAL or EDGE inputs** and were dropped by the registered copy rule (the rule the owner's tour obeys), leaving 36. The owner (oracle) answered them; the answers became 19 visible tests.
- **Teams** (3 builders each, no questions): **N0**; **T** (owner's tour, 50 examples); **H** (`HANDBOOK.md`); **X** (the 36 answered extractor inputs, same ask text as T).
- **Hidden suite.** 500 tests (seed 15200000), 70% edge calls. Not committed.

| Team | Gets | Builder cost | Visible | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | nothing | $2.09 | 1,380/1,380 | **223/500 (44.6%)** | 33.8–56.2% | |
| H | handbook | $2.05 | 1,380/1,380 | **386/500 (77.2%)** | 64.8–88.8% | +32.6 (CI +21.2 to +44.2) |
| X | extracted tour (36) | $2.18 | 1,399/1,399 | **403/500 (80.6%)** | 71.2–89.2% | +36.0 (CI +24.4 to +48.2) |
| T | owner's tour (50) | $2.42 | 1,407/1,407 | **463/500 (92.6%)** | 85.4–98.0% | +48.0 (CI +32.4 to +61.0) |

Rule-giver $1.52, extractor $0.26; total $10.52 at list price. Paired: X − H **+3.4** (CI −5.0 to +15.0); T − X **+12.0** (CI −0.4 to +23.6).

**Validity.** One kept extractor input is a strict near copy of an EDGE input (`initials`: `'  ada   lovelace '` against `'  Ada   Lovelace '`). Every team fixed that function fully, so it does not affect the comparison.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| X1 | X − N0 ≥ 0.5 × (T − N0) | **Held**: +36.0 against +24.0 (X keeps **0.75** of the tour gain) |
| X2 | X ≥ H | **Held**: +3.4 (interval includes 0, so weak) |
| X3 | T − X ≥ +5 | **Held**: +12.0 |
| X4 | X fixes ≥ 0.15 more where no decision is omitted | **Held**: 1.00 against 0.70 (+0.30); H: 1.00 against 0.60 |
| X5 | ≥ 40 extracted inputs kept; every team passes its visible tests | **Failed** on the first part: 36 kept, because 14 picks were exact hidden-test inputs. Visible tests all pass |
| X6 | N0 below 70% | **Held**: 44.6% |
| Kill | X − N0 < 0.25 × (T − N0) | **Did not fire** |
| Rule | X1 and X2 hold: "documents → extractor → owner answers" becomes the practical first step | **Fired** |
| Rule | H ≥ T − 5 would mean the example format adds little | **Did not fire** (H is 15.4 below T) |

## What it means

### 1. The extractor points nearly where the owner's own QA points

28% of the extractor's 50 picks (14) were *exactly* inputs on the owner's own edge list: `mask_card('4111-1111-1111-1111')`, `grade_letter(89.5)`, `discount_price(100, -10)`. Two agents, one reading only the handbook, converged on the same probing points. The copy rule dropped them, so **X is a conservative estimate**: in real use those examples would stay.

### 2. Where each path wins and loses (N0 edge errors fixed; c = clear, v = vague, o = omitted)

| Function | Decisions | N0 errors | T | H | X |
| --- | --- | --- | --- | --- | --- |
| phone_format | c o | 31 | 31 | **0** | **31** |
| split_bill | c o v | 24 | 24 | 5 | 14 |
| invoice_number | o | 11 | 11 | 0 | 0 |
| mask_card | o v | 15 | 15 | 3 | 0 |
| sku_normalize | c v o | 23 | 23 | 3 | 3 |
| grade_letter | c o v | 30 | 26 | 19 | 14 |
| prorate_rent | c v c | 19 | 13 | **19** | **19** |
| days_overdue | c c | 16 | 11 | **16** | **16** |

- Where a function's decisions are all written down, the handbook paths beat the owner's tour (`prorate_rent`, `days_overdue`). Prose carries the whole rule; one example per decision sometimes doesn't.
- Where a decision is omitted, only the owner's tour reliably gets it. The extractor occasionally guesses where an unwritten decision sits and lets the owner's answer fill it in (`phone_format`).

### 3. A simple model of the three paths (conjecture)

Edge errors fixed ≈ the share of decisions the source exposes, times how well that format transfers:

| Path | Exposes | Measured share fixed (N0 edge errors) |
| --- | --- | --- |
| Owner's tour | all decisions | 0.98 (Gate 14), 0.94 here |
| Handbook | clear and some vague; not omitted | 0.65 |
| Extracted tour | clear, vague, plus some omitted it suspects | 0.74 |

## Design consequences for Hive's intent interface

1. **When the owner can list their decisions:** the owner's tour (Gates 13 to 15: 89–96%).
2. **When the owner has documents:** an extractor reads them and picks examples; the owner answers; the answers become tests (80.6% here, a conservative estimate). Do not just hand builders the documents (77.2%).
3. **Unwritten decisions are the remaining floor.** Next to test: stack the handbook, the extracted tour and builder questions, and see whether together they close most of the 12-point gap to the owner's own tour.

## Honest odds

- Handbook plus extracted tour plus 17 questions reaches 90% hidden: about 50%.
- The extracted tour keeps ≥ 0.5 of the tour gain on another rule set: about 70%.

## Limits

- One run per team, one rule set. The two key differences (X − H, T − X) have intervals that touch zero.
- The handbook was written by the same agent that wrote the rules, told exactly how much to leave out. Real handbooks may be worse, or contradict the policy (Gate 7).
- The extractor, rule-giver and builders are the same kind of model.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md`, `prompts/rulegiver_brief.md`, `prompts/extractor_brief.md` | Predictions, rules and briefs, pushed before the rules existed |
| `referee/analyze.py` | Registered analysis (committed before the run) |
| `referee/oracle.py` | Rules, decisions, tour, handbook and handbook status, unsealed after scoring (synthetic) |
| `results/xtour_inputs.json`, `results/extractor/` | The extractor's 50 picks (kept and dropped) and its raw output |
| `results/` | Summary, analysis output, probes, cost per worker, run log, rule-giver output |
| `swarms/*.bundle`, `logs/` | All four teams' histories; worker logs |
