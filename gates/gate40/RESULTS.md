# Gate 40 results: unusual input as owner decisions, Oct 29 2026

**Question.** In Gate 39, Hive's interview never asked 8 of 25 decisions, all about unusual input. Does telling the planner to list unusual input as owner decisions, with up to 30 questions, close that gap?

**Answer.**
- **No. Coverage did not rise.** The changed interview (H2) planned 40 decisions and wrote 27 questions. Then it skipped 8 as "settled by an earlier answer", asked about 16 of the 25 declared decisions (H: 19), and scored 64.4% against H's 63.2% (+1.2, CI −11.6 to +15.2). The change does not ship.
- **The ceiling replicated: the complete rule sheet passed 250 of 250 again** and broke nothing. Over two rule sets that is 500 of 500 hidden tests and 0 broken calls. It beat the decision tour by 16 points (84.0%).
- **The bigger leak is now clear: what the interview writes down does not survive to the sheet.** Of the decisions its questions were about, the sheet stated 0.74 right (H) and 0.69 (H2), after 0.76 in Gate 39. That is despite Gate 39's fixes. Two steps lose them:
  - **The merge.** Hive folds all his answers into about 11 general rules, one per function, and branches drop out.
  - **"Settled" skips.** A question is skipped when an earlier answer is taken to settle it. In H2, "only the last 4 digits are shown" was taken to settle "a card number typed with only 3 digits", so that question was never put to him.
- **Next (Gate 41):** one interview and two hand-overs. Builders get the general sheet alone, or the sheet plus every ruling he gave, kept whole. This isolates the merge; skipped questions are counted from the transcript.

## Setup

- **Rules.** A fresh independent rule-giver with Gate 39's brief: 10 functions, 25 declared decisions. Not edited. Predictions and analysis pushed before the rules existed (`8a8d49a`).
- **Suites.** Visible seed 40100. Hidden 250 tests (seed 40200000, 70% edge calls), not committed.
- **Synthetic owner.** As in Gate 39, but he now sees his whole terminal history. That fixes Gate 39's harness defect.
- **Interviews** (two separate runs, same owner, `hive.interview.interview` with Gate 39's fixes):
  - **H**, as shipped: planned 23 decisions, 19 questions, 2 skipped as settled, 29 owner replies, 11 rules.
  - **H2** (`inputs=True`, up to 30): planned 40 decisions, 27 questions, 8 skipped as settled, 28 owner replies, 11 rules.
- **Teams** (3 builders each, no questions): **N0**; **H**; **H2**; **R** (the owner's complete sheet, 64 rules); **T** (decision tour, 25 examples).

| Team | Builder cost | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- |
| N0 | $0.50 | **104/250 (41.6%)** | 25.2–60.0% | |
| H | $0.59 | **158/250 (63.2%)** | 48.4–80.0% | +21.6 (CI +4.8 to +37.6) |
| H2 | $0.69 | **161/250 (64.4%)** | 44.4–84.4% | +22.8 (CI +6.0 to +40.4) |
| R | $0.66 | **250/250 (100%)** | 100–100% | +58.4 (CI +39.6 to +74.8) |
| T | $0.54 | **210/250 (84.0%)** | 67.6–96.8% | +42.4 (CI +24.4 to +60.8) |

- **Share of N0's 193 wrong edge calls fixed:** H 0.55, H2 0.42, R 1.00, T 0.83.
- **N0-right edge calls broken (of 253):** H 21, H2 15, R 0, T 18.
- **Other costs:** rule-giver $0.32, documenter $0.14, owner $2.10 (H) and $2.04 (H2), judge $0.23. Hive's own model calls were not metered. Builders ran on Sonnet 5.5, as in Gate 39.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| G1 | Coverage H2 ≥ 0.85 and H ≤ 0.75 | **Failed:** H2 0.64, H 0.76 |
| G2 | H2 − H ≥ +8 | **Failed:** +1.2 (CI −11.6 to +15.2) |
| G3 | Transfer ≥ 0.85 in H and H2 | **Failed:** 0.74 and 0.69 |
| G4 | R ≥ 95% | **Held:** 100% |
| G5 | R − T ≥ +10 | **Held:** +16.0 |
| G6 | H2's owner replies ≤ 1.6 × H's | **Held:** 28 vs 29 |
| G7 | N0 below 65% | **Held:** 41.6% |
| Kill | H2 ≤ H | **Did not fire** (+1.2, inside noise) |
| Ship rule | H2 − H ≥ +5 and coverage up | **Did not fire:** `inputs=True` stays off |

## What it means

### 1. Asking for more questions did not ask more

H2's planner listed 40 decisions instead of 23, but the questions it wrote were not aimed at the declared decisions any better. For example, it asked about card masking in general rather than about letters or short numbers. Hive's "settled by an earlier answer" step then skipped 8 of its 27 questions, against 2 of H's 19. Two runs of the same shipped interview asked about 17 (Gate 39) and 19 (here) of 25 decisions. **Coverage moves with each interview's luck more than with this prompt.**

### 2. The sheet loses about a quarter of what he said, in three runs

| Run | Decisions asked | Stated right on the sheet | Share |
| --- | --- | --- | --- |
| Gate 39, H | 17 | 13 | 0.76 |
| Gate 40, H | 19 | 14 | 0.74 |
| Gate 40, H2 | 16 | 11 | 0.69 |

The judge counted a decision as asked when any written question was about it, including questions later skipped as settled, so this share mixes two losses. Every sheet held about 10 or 11 general rules, roughly one per function. Hive's rule-sheet step merges all of a function's answers into one "Whenever …" rule, and branches drop out: the surcharge amount, the tie rule for ratings. In one case it hedged ("an A, because we round up, or because our cut-offs are lower"). The other loss is the settled skip: 8 of H2's 27 questions and 2 of H's 19 were never put to him, and at least one (card numbers too short to be real) was not settled by the answer that skipped it. The interview's rules also broke 15 to 21 calls that N0 had right. The complete sheet broke none, so stretched or vague rules cost points as well as missing ones.

### 3. What holds across both wind-tunnel runs

| | Gate 39 | Gate 40 |
| --- | --- | --- |
| Complete sheet (R) | 250/250, 0 broken | 250/250, 0 broken |
| Decision tour (T) | 75.6% | 84.0% |
| Hive's interview (H) | 76.0% | 63.2% |
| No owner (N0) | 38.4% | 41.6% |
| Interview's gain as a share of the complete sheet's | 0.61 | 0.37 |

**Established on two rule sets (synthetic owner):** builders execute a complete written rule sheet without error. **Model:** an intent channel's value is the share of decisions it delivers stated whole. Hive's interview delivers about half of them (coverage about 0.7, then about 0.72 kept).

## Turned into the product

- `inputs=True` stays off by default; the shipped interview is unchanged by this gate.
- The finding for the product is the transfer loss. Gate 41 tests the fix before it ships.

## Limits

- One interview per interview arm, so H against H2 carries each interview's luck, as the power note warned. The two runs of the shipped interview differ by 13 points (76.0 vs 63.2) on different rule sets.
- The owner is synthetic. Some loss sits in his answers: he answered "80 kg costs 148 dollars" without stating the surcharge rule inside that number. Gate 41 measures how much of the loss is the owner's wording and how much is the merge.
- Same model family throughout.

## Files

As in Gate 39: `prompts/`, `referee/` (wind tunnel, analysis, unsealed oracle), `results/` (summary, analysis, probes, costs, both interviews' transcripts, sheets and questions, judge labels), `swarms/`, `logs/`.
