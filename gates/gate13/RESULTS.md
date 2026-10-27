# Gate 13 results: the owner's decision tour vs builder questions, Oct 27 2026

**Question.** Gate 12 found a floor: about a fifth of the errors were never fixed, however many questions builders got, because they sat at decisions no builder thought to probe. If the product owner points instead (one worked example per policy decision, given as tests), does that beat the same number of answers at points the builders chose?

**Answer.**
- **Yes, by a wide margin.** 50 owner-chosen examples lifted hidden correctness from 57.8% to **89.4%**. Up to 51 builder-chosen answers (17 questions) reached **67.2%**. Tour plus questions reached **95.2%**, the highest in any intent gate.
- **The tour reaches what questions cannot.** Of the 139 edge calls wrong both with no questions and with 17 questions, the tour team got **91%** right.
- **Every registered prediction held** (M1 to M5). By the pre-registered rule, the decision tour becomes the first step of Hive's intent interface.
- **Its failure mode is over-generalization.** Shown one leniency, builders loosened neighbouring rules. Questions on top of the tour repaired most of that (broken calls 27 with the tour alone, 15 with the tour plus questions).

## Setup

- **Rules.** A fresh independent rule-giver: Gate 12's brief (1 to 4 declared decisions per function, five functions each), plus one example per decision (`DECISION_EXAMPLES`, 50 in all), checked by `run_gate.py` to be disjoint from TYPICAL and EDGE. Not edited. Predictions and analysis code were pushed before the rules existed (commit 6ba9283).
- **The tour.** The 50 examples became 27 visible tests (`<function>_tour_<n>.json`) in the starting repo of teams T and TQ only.
- **Teams** (3 builders each, same prompt): **N0** (nothing), **T** (tour), **Q** (17 questions for the team), **TQ** (tour and 17 questions).
- **Hidden suite.** 500 tests (seed 13200000), 70% edge calls, drawn only from TYPICAL and EDGE inputs. Not committed.

| Team | Owner examples | Questions used | Builder cost | Visible | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| N0 | 0 | 0 | $1.85 | 1,380/1,380 | **289/500 (57.8%)** | 45.6–69.6% | |
| Q | 0 | 17 of 17 | $2.17 | 1,380/1,380 | **336/500 (67.2%)** | 57.6–77.2% | +9.4 (CI −0.6 to +20.2) |
| T | 50 | 0 | $2.56 | 1,407/1,407 | **447/500 (89.4%)** | 80.4–96.4% | **+31.6** (CI +15.6 to +45.8) |
| TQ | 50 | 17 of 17 | $2.39 | 1,407/1,407 | **476/500 (95.2%)** | 89.4–100.0% | **+37.4** (CI +22.8 to +51.4) |

Rule-giver $0.83; total $9.80 at list price.

## Validity checks (done before reading the result as real)

- **No hidden test was copied.** 0 of 158 hidden edge inputs is a strict near copy of a tour input: equal after removing case, spaces and dashes, or numbers within 1%. (A looser first check, "differs in at most one argument", flagged 49%. It is meaningless for one-argument functions and was discarded.)
- **No hardcoding.** 35 distinctive tour strings were searched for in every team's engine source. The only hits are tier names (`silver`, `bronze`), which appear in the spec and in all teams.
- **Treatment delivered.** T and TQ pass all 27 tour tests. Q and TQ each used all 17 questions.

## Predictions scored (registered code: `referee/analyze.py`)

| # | Prediction | Result |
| --- | --- | --- |
| M1 | fixed_T / fixed_Q ≥ 1.3 | **Held**: 195 / 72 = **2.71** (95% CI 1.13 to 13.5, bootstrap over functions) |
| M2 | TQ fixes ≥ 0.80 of N0's edge errors | **Held**: **0.89** (Gate 12's best, 80 questions: 0.76) |
| M3 | Of edge calls wrong in N0 and Q, T gets ≥ 0.50 right | **Held**: **0.91** (TQ 0.91) |
| M4 | Q and TQ use ≥ 15 of 17; T and TQ pass every tour test | **Held**: 17 and 17; 27/27 and 27/27 |
| M5 | N0 below 70% hidden | **Held**: 57.8% |
| Kill | fixed_T ≤ fixed_Q | **Did not fire** |
| Rule | M1 and M3 hold: the tour becomes step one of the intent interface | **Fired** |

The M1 interval is wide because Q fixed little (72 errors). The point estimate depends on 17 questions being a small budget, so the comparison to remember is "50 owner-chosen values vs 51 builder-chosen values".

## What it means

### 1. Information is not the bottleneck; the pointer is

Both teams received about 50 answered values. Placed by the builders, they fixed 0.28 of N0's edge errors. Placed by the owner, 0.76. Same channel and budget; the only difference is who chose the inputs. This completes Gate 12's reframing. Builders' questions explore the region they can imagine; the owner's examples land on the decisions themselves, including the ones nobody imagines.

Per function (N0 edge errors, then errors fixed by T / Q / TQ). Rows where questions did little and the tour fixed everything:

| Function | N0 errors | T | Q | TQ |
| --- | --- | --- | --- | --- |
| grade_letter | 14 | +14 | 0 | +14 |
| rating_stars | 22 | +22 | 0 | +22 |
| discount_price | 17 | +17 | +4 | +17 |
| age_years | 13 | +13 | +3 | +13 |
| late_fee | 22 | +22 | +9 | +22 |
| due_date | 32 | +32 | +20 | +32 |

The full table is in `results/analysis.txt`.

### 2. One example per decision teaches the rule (mostly), not just the point

Gate 4 found that "an answer pins a point, not a rule". Here a single example per decision generalized to hidden inputs that were never near copies. For example, `grade_letter`'s one tour example (105 → A+) carried over to the hidden 100.5. The likely reason: each example was chosen by the person who knows the rule, so it lands where the rule bites and shows its direction.

### 3. Over-generalization is the tour's failure mode, and questions repair it

| Team | Edge calls fixed | Edge calls broken (right in N0, wrong here) |
| --- | --- | --- |
| Q | 116 | 44 |
| T | 222 | 27 |
| TQ | 242 | **15** |

The worst case is `mask_card`. Its one decision is "spaces and dashes are stripped". After the tour, T also accepted `'abcd1234'`, `''` and dotted numbers, which policy maps to NULL (−21 calls). In `days_between`, "order of dates ignored" spread into lenient date parsing. Builders read one leniency as a lenient owner. Breakage is not specific to the tour: Q's questions broke more calls (44). Questions on top of the tour gave the fewest breaks.

## Design consequences for Hive's intent interface

1. **Step one: the owner gives a decision tour,** one worked example per policy decision, as tests. Established here for one rule set, one run per team.
2. **Step two: builders ask questions around it.** They repair over-generalization and fill gaps (95.2% with both).
3. **Next fix to test:** pair each tour example with a *contrast*, a nearby input the decision does not cover, so a leniency is not stretched.
4. **Open, and the real-world crux:** here the owner was an agent that knew every decision it wrote. A human owner may not know all their own decisions (Gate 7: the company's documents overturned two of the owner's rules). How to produce a tour cheaply and completely is now the main problem.

## Honest odds

- The tour's advantage replicates on a new rule-giver (T − N0 ≥ +20 points): about 80%.
- Contrast pairs halve tour-caused breakage: about 50%.
- A real person's tour is as complete as an agent's: low, perhaps 30%. This is the idea's real risk.

## Limits

- One run per team, one rule set.
- The rule-giver wrote the tour, the EDGE list and the decisions, so the hidden suite is the owner's own QA list. Real acceptance is also the owner's intent, but an owner who forgets a decision would leave it out of both.
- The rule-giver is the same kind of model as the builders.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md`, `prompts/rulegiver_brief.md` | Predictions, decision rules and brief, pushed before the rules existed |
| `referee/analyze.py` | Registered analysis (committed before the run) |
| `referee/oracle.py` | Rules, declared decisions and the tour, unsealed after scoring (synthetic) |
| `results/` | Summary, analysis output, every question and answer, probes, cost per worker, run log, rule-giver output |
| `swarms/*.bundle`, `logs/` | All four teams' histories; worker logs |
