# Gate 41 results: keep every ruling whole, Oct 29 2026

**Question.** Hive's rule sheet stated right only 0.69 to 0.76 of the decisions its interview asked about (Gates 39, 40). Is the loss in Hive's merge into one rule per function? If so, giving builders every ruling whole, beside the sheet, should recover it.

**Answer.**
- **No: the kill fired.** From one interview, the sheet alone (H) scored 72.8%; the sheet plus every ruling kept whole (K) scored 66.0%. The difference is −6.8 points (CI −16.0 to +0.8). K broke 16 of N0's correct edge calls, against H's 6: builders stretched the raw rulings.
- **The merge was not the leak here.** The judge found H and K stated exactly the same decisions right (10 of 25, 4 partly), so the sheet lost nothing he had said.
- **The leak is upstream, in two places:**
  - **Coverage.** The questions were about only 11 of 25 decisions. The planner listed 40 decisions, but the interview wrote just 15 questions and skipped 1 as settled.
  - **His answers cover one case, not the whole decision.** Of the 11 decisions asked, his answers stated 7 whole and 4 in part. Asked about zero reviews, he answered for zero reviews, but the rule is "fewer than 3". Asked about a foreign number, he answered for a foreign number, not for numbers with the wrong digit count. A question about a case gets an answer about that case.
- **The ceiling held a third time:** the complete rule sheet passed 250 of 250 and broke nothing. That makes 750 of 750 over three rule sets.

## Setup

- **Rules.** A fresh independent rule-giver (Gate 39's brief): 10 functions, 25 declared decisions. Not edited. Predictions pushed before the rules existed (`d27a1cc`).
- **Suites.** Visible seed 41100; hidden 250 tests (seed 41200000, 70% edge calls), not committed.
- **One interview**, as shipped, answered by the synthetic owner with his whole terminal in view:
  - 40 planned decisions, 15 questions (1 skipped as settled), 24 owner replies, 4.6 minutes;
  - 14 rulings, merged into an 11-rule sheet.
- **Teams** (3 builders each, no questions):
  - **N0:** nothing extra.
  - **H:** `instructions(sheet)`.
  - **K:** `instructions(sheet, rulings)`: the sheet, then his answers word for word, with "where an answer says more than the rules, the answer holds".
  - **R:** the owner's complete sheet, 68 rules.

| Team | Builder cost | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- |
| N0 | $0.69 | **109/250 (43.6%)** | 30.0–57.2% | |
| H | $0.72 | **182/250 (72.8%)** | 54.4–89.6% | +29.2 (CI +15.6 to +41.6) |
| K | $0.71 | **165/250 (66.0%)** | 45.6–84.8% | +22.4 (CI +7.2 to +37.6) |
| R | $0.52 | **250/250 (100%)** | 100–100% | +56.4 (CI +43.2 to +70.4) |

- **Share of N0's 185 wrong edge calls fixed:** H 0.58, K 0.49, R 1.00.
- **N0-right edge calls broken (of 262):** H 6, K 16, R 0.
- **Other costs:** rule-giver $0.36, documenter $0.16, owner $1.69, judge $0.17.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| K1 | K − H ≥ +5 | **Failed:** −6.8 (CI −16.0 to +0.8) |
| K2 | K keeps ≥ 0.90 of asked decisions and H ≤ 0.80 | **Failed:** both 0.73 |
| K3 | K breaks at most 5 more N0-right calls than H | **Failed:** 16 vs 6 |
| K4 | R ≥ 95% | **Held:** 100% |
| K5 | His answers state ≥ 0.85 of the asked decisions right | **Failed:** 0.64 (7 of 11) |
| K6 | N0 below 65% | **Held:** 43.6% |
| Kill | K ≤ H | **Fired:** whole rulings are not handed to builders |

## What it means

1. **Rulings at single cases are stretched.** "Zero reviews → show nothing" sitting next to the sheet's general rule led builders to change behaviour around it. This repeats Gates 4 and 28. A general rule is the right thing to hand over; a list of case rulings is not.
2. **A question about a case returns a rule about that case.** Gates 39 to 41 together:

| | Gate 39 | Gate 40 (H) | Gate 41 |
| --- | --- | --- | --- |
| Decisions the questions were about | 17 of 25 | 19 | 11 |
| Stated right on the sheet | 13 | 14 | 10 |
| Interview's gain as a share of the complete sheet's | 0.61 | 0.37 | 0.52 |

The interview misses decisions it never asks about, and states only part of the ones it asks about through one case. Both losses come from the same source: Hive learns a decision through examples the owner answers, so it gets only the parts those examples touch. A complete sheet gives every decision whole, and builders execute it perfectly.

3. **Next: make the sheet complete by construction.** The built code already decides every case, including the unusual ones nobody asked about. A sheet written from the code, every branch as a plain rule, is complete on day one. The owner then only has to mark the rules that are wrong and say the right one. That turns elicitation, which misses, into verification, where the remaining limit is his attention. Gate 42 tests it with the same synthetic owner.

## Turned into the product

- `instructions(rules, rulings)` stays in the code but unused: `hive start` keeps handing over the general sheet only. Recorded as "not used" in `docs/research_to_product.md`.

## Limits

- One interview and one run per team. Its coverage (11 of 25) was the lowest of three interviews.
- Synthetic, perfectly consistent owner, told to answer only what is asked. A real owner may volunteer more, or less.
- Same model family throughout.

## Files

As in Gate 40: `prompts/`, `referee/` (wind tunnel, analysis, unsealed oracle), `results/` (summary, analysis, probes, costs, the interview's transcript, sheet and questions, judge labels, the three hand-overs), `swarms/`, `logs/`.
