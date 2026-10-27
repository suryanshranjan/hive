# Gate 17 results: documented owner vs listing owner, same rules, fair copy rule, Oct 27 2026

**Question.** On the same rules, how far apart are the two versions of Hive's intent interface: an owner who lists their decisions (own tour + questions) and an owner who only has documents (handbook + extracted tour + questions)? And how large is the extracted tour's gain once the copy rule stops penalizing it?

**Answer.**
- **Both interfaces now reach the 90s.** Hidden correctness: nothing 46.4%, extracted tour **87.8%**, documented owner (handbook + extracted tour + 17 questions) **93.8%**, listing owner (own tour + 17 questions) **98.2%**, the highest in any gate.
- **The gap between the owners is small and uncertain:** TQ − HXQ = **+4.4** (CI −2.4 to +11.4). That is between the registered decision thresholds (+3 and +5), so neither rule fires. Whether drawing a decision list out of a person is worth building stays open on this evidence.
- **The whole remaining gap sits at decisions nobody wrote down.** On functions with an omitted decision, documents fixed 0.86 of N0's edge errors and the owner's own list 1.00. Everywhere else, both fixed 1.00.
- F1, F3, F4, F5 and F6 held; F2 failed (+4.4 against the +5 threshold).

## Setup

- **Rules and extractor.** A fresh independent rule-giver (Gate 15's brief; handbook 20 clear, 15 vague, 15 omitted). The extractor ($0.22) picked 50 inputs from the handbook and spec.
- **Fair copy rule** (new). All 50 picks were kept. **6** equalled a hidden-suite input; those 6 calls were removed from scoring for every team, so nothing was copied and nothing penalized. (Gates 15 and 16, under the old rule, dropped 14 and 17 picks.)
- **Teams** (3 builders each): **N0**; **X** (extracted tour); **HXQ** (handbook + extracted tour + 17 questions); **TQ** (owner's tour + 17 questions). Predictions and analysis code were pushed before the rules existed (commit d55cd46).
- **Hidden suite.** 500 tests (seed 17200000), 70% edge calls, minus the 6 excluded calls. Not committed.

| Team | Owner has | Builder cost | Visible | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- | --- | --- |
| N0 | | $2.06 | 1,380/1,380 | **232/500 (46.4%)** | 36.4–56.6% | |
| X | documents (examples only) | $2.08 | 1,403/1,403 | **439/500 (87.8%)** | 80.0–94.6% | +41.4 (CI +32.8 to +49.4) |
| HXQ | documents | $2.15 | 1,403/1,403 | **469/500 (93.8%)** | 88.0–98.6% | +47.4 (CI +38.0 to +56.2) |
| TQ | a decision list | $2.49 | 1,407/1,407 | **491/500 (98.2%)** | 94.6–100.0% | +51.8 (CI +41.6 to +61.8) |

Rule-giver $1.24, extractor $0.22; total $10.23 at list price. One N0 worker ran 12.4 minutes (others 2 to 7); all exited cleanly.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| F1 | X − N0 ≥ +30 | **Held**: +41.4 (CI +33.0 to +49.2) |
| F2 | TQ − HXQ ≥ +5 | **Failed**: +4.4 (CI −2.4 to +11.4) |
| F3 | HXQ ≥ 85% | **Held**: 93.8% |
| F4 | TQ ≥ 92% | **Held**: 98.2% |
| F5 | ≥ 15 of 17 questions used by HXQ and TQ; visible tests pass | **Held**: 17 and 17; all pass |
| F6 | N0 below 70% | **Held**: 46.4% |
| Rule | TQ − HXQ < +3: no elicitation step needed | **Did not fire** |
| Rule | TQ − HXQ ≥ +5: build and test an elicitation step with people | **Did not fire** |
| Rule | X − N0 < +20: extracted tour weak | **Did not fire** |

## What it means

### 1. How much of the extracted tour's jump is the fairer rule?

| Gate | Copy rule | Picks overlapping the hidden suite | X − N0 |
| --- | --- | --- | --- |
| 15 | drop | 14 (dropped) | +36.0 |
| 16 | drop | 17 (dropped) | +19.4 |
| 17 | exclude from hidden | 6 (kept; calls not scored) | **+41.4** |

Under the old rule this gate would have dropped only 6 picks, so the fairer rule explains only part of the rise. The rest is rule-set variance (the extractor's gain ranges from +19 to +41 across three rule sets). The fair rule remains the right one: it never penalizes good targeting.

### 2. The remaining gap is exactly the unwritten decisions

Share of N0's edge errors fixed:

| Team | Functions with an omitted decision (237 errors) | Functions without (100 errors) |
| --- | --- | --- |
| X | 0.86 | 1.00 |
| HXQ | 0.86 | 1.00 |
| TQ | **1.00** | 1.00 |

Handbook and questions on top of the extracted examples added +6.0 points of hidden pass (CI −1.8 to +13.8), but did not move the omitted-decision share. Only the owner's own list reached those decisions.

### 3. The measured interface, across Gates 12 to 17

| Owner has | Interface | Hidden pass | Gates |
| --- | --- | --- | --- |
| A decision list | own tour + 17 questions | **95.2%, 98.2%** | 13, 17 |
| A decision list | own tour | 89.4%, 95.6%, 92.6% | 13, 14, 15 |
| Documents | handbook + extracted tour + 17 questions | 83.2% (old copy rule), **93.8%** | 16, 17 |
| Documents | extracted tour | 80.6%, 60.8% (old rule), **87.8%** | 15, 16, 17 |
| Documents | handbook only | 77.2% | 15 |
| Nobody writes anything | builder questions only (17 to 80) | 67.2% to 81.6% | 12, 13 |
| Nothing | | 36.6% to 57.8% | all |

## Design consequences: Hive's intent interface as measured

1. **If the owner can list their decisions:** they give one worked example per decision (the tour); builders ask about 17 questions around it; answers become tests. 95 to 98% hidden.
2. **If the owner has documents:** an extractor reads them and picks one input per decision it finds or suspects; the owner answers; ship the handbook, the answered examples and builder questions. 94% hidden here.
3. **The difference is the decisions nobody wrote down.** Closing it needs the owner's own knowledge. Whether a cheap elicitation step ("here are the decisions we found; which are missing?") recovers it is the next question, and it needs real people. Every owner in this lab has been an agent that knew its own rules.

## Honest odds

- The documented-owner stack stays at or above 88% on a new agent-written rule set: about 70%.
- With a real company's documents and a real person answering, it stays above 80%: unknown; perhaps 50%. Gate 7 (real company, no tour) reached 49.6% with 15 answered questions.

## Limits

- One run per team. TQ − HXQ's interval spans −2.4 to +11.4.
- The handbook, rules and tour all come from one agent. It was told how much to omit; a real handbook's gaps are not chosen.
- Extractor, rule-giver and builders are the same kind of model.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions and decision rules, pushed before the rules existed (briefs reused from `gates/gate15/prompts/`) |
| `referee/analyze.py` | Registered analysis (committed before the run) |
| `referee/oracle.py` | Rules, decisions, tour, handbook and status, unsealed after scoring (synthetic) |
| `results/hidden_exclude.json`, `results/xtour_inputs.json`, `results/extractor/` | Excluded calls, extractor picks, raw extractor output |
| `results/` | Summary, analysis output, every question and answer, probes (already filtered), cost per worker, run log, rule-giver output |
| `swarms/*.bundle`, `logs/` | All four teams' histories; worker logs |
