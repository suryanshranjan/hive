# Gate 42 results: a rule sheet complete by construction, Oct 29 2026

**Question.** Questions about cases deliver about half of an owner's decisions whole (Gates 39–41). Can Hive do better by writing the rule sheet from the first build's code, every behaviour as a rule, and asking the owner only to mark what is not his policy?

**Answer.**
- **Yes, with a synthetic owner.** Fresh builders given the corrected code sheet (C) passed **249 of 250** hidden tests (99.6%) and broke 1 correct call. The owner's own complete sheet (R) scored 100%, Hive's interview (H) 68.4%, and no owner (N0) 38.8%. **C − H = +31.2 points (CI +15.2 to +49.6).** The ship rule fired.
- **Why it works:**
  - The code sheet asks about everything the code does. Every rule is a whole, general statement, so his corrections come back whole too.
  - It addressed 20 of 25 decisions before review, 18 of them wrongly. That is the point: N0 guessed, and the sheet exposed each guess.
  - The owner repaired 16 of the 18 and added the 5 missing ones in his "anything missing?" answer. He spoiled none that were right.
- **The cost moved to the owner's reading:** 68 rules, 34 marked wrong and rewritten, and one long "missing" answer, in 36 replies. This owner reads every rule and knows his policy exactly. Whether a real owner will read and correct a 68-rule sheet is the open question (Gates 30–35: real owners audit long lists of builder decisions poorly). His business usually differs from the defaults far less than this rule-giver's does (Gate 28: 1 of 15).

## Setup

- **Rules.** A fresh independent rule-giver (Gate 39's brief): 10 functions, 25 declared decisions. Not edited. Predictions pushed before the rules existed (`a21ce06`).
- **Suites.** Visible seed 42100; hidden 250 tests (seed 42200000, 70% edge calls), not committed.
- **Stage 1:** N0 builds (3 builders).
- **The code sheet:**
  - **D.** A describer agent read and ran N0's built code, never the oracle, and wrote 68 rules ($0.34).
  - **C.** In a fresh terminal the synthetic owner saw D through Hive's own `interview.confirm_sheet`. He marked 34 rules and said each one right, each amended rather than replaced, then answered "anything missing?" (69 rules, $3.36).
- **H:** one interview as shipped: 19 questions, 3 skipped as settled, 31 owner replies, 10 rules ($2.32).
- **R:** the owner's complete sheet, 68 rules.
- **Stage 2 teams:** H, C and R, 3 builders each, fresh from the starting repo, no questions.

| Team | Builder cost | Hidden tests | 95% CI by function | vs N0 |
| --- | --- | --- | --- | --- |
| N0 | $0.70 | **97/250 (38.8%)** | 22.4–55.6% | |
| H | $0.63 | **171/250 (68.4%)** | 50.4–84.4% | +29.6 (CI +11.2 to +48.8) |
| C | $0.76 | **249/250 (99.6%)** | 98.8–100% | +60.8 (CI +42.8 to +77.2) |
| R | $0.62 | **250/250 (100%)** | 100–100% | +61.2 (CI +44.0 to +77.2) |

- **Share of N0's 213 wrong edge calls fixed:** H 0.72, C 1.00, R 1.00.
- **N0-right edge calls broken (of 236):** H 30, C 1, R 0.
- **Other costs:** rule-giver $0.38, documenter $0.14, judge $0.29.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| C1 | D addresses ≥ 90% of decisions | **Failed:** 0.80 (20 of 25). Missing: the late fee's minimum and cap, the weekend rule for due dates, a rounding step for ratings, and name particles for initials. N0's code had none of these, so there was nothing to describe. |
| C2 | C states ≥ 85% right, and H ≤ 60% | **Failed on H:** C 0.92 (23 of 25), H 0.72 |
| C3 | C − H ≥ +10 | **Held:** +31.2 |
| C4 | C ≥ 90% | **Held:** 99.6% |
| C5 | R ≥ 95% | **Held:** 100% (fourth rule set) |
| C6 | Review repairs ≥ 80% of D's wrong or partial | **Held:** 16 of 18 (0.89) |
| C7 | N0 below 65% | **Held:** 38.8% |
| Kill | C ≤ H | **Did not fire** |
| Ship | C − H ≥ +5 | **Fired** |

## What it means

1. **Complete by construction, almost.** The sheet describes what the code does, so it covers every behaviour the code has. It cannot describe a behaviour the code lacks: a cap or a weekend rule that N0 never wrote. Those 5 decisions came back only because the owner answered "anything missing?" in full. The repair rate is the honest measure: 16 of 18 wrong rules fixed, 5 of 5 absent ones added, 0 right ones spoiled. The remaining 2 sit in card masking, where his corrections left two rules in conflict. The builders still fixed all of that function's errors.
2. **Verification beats elicitation, for this owner.** Asked to recall, the owner gave rules about the cases he was shown (Gate 41: 7 of 11 whole). Shown a full rule, he could say what was wrong with it and give the whole rule back. Over four rule sets the evidence is one line:

| Delivered to builders | Hidden pass |
| --- | --- |
| Nothing | 38–44% |
| Interview rules (as shipped) | 63–76% |
| Decision tour, one example per decision | 76–84% |
| **Code sheet, corrected by the owner** | **99.6%** |
| Owner's complete sheet | 100% (four times) |

3. **The real risk is the owner's attention.** This owner marked half the sheet wrong because the rule-giver was told to make every decision unguessable. A real owner's code sheet would mostly confirm defaults: in Gate 28, 14 of 15 of the founder's verdicts matched the builders. That means fewer corrections but the same reading. And Gates 30–35 found real owners audit long lists of builder decisions poorly. The difference here is that the list is *his rules* in his words, not builders' technical assumptions. In Gate 38, day 1, the founder confirmed a 13-rule sheet and corrected one rule. Whether that holds at 60 rules is the next test, and it needs the founder.

## Turned into the product (this commit)

- **New `hive/codesheet.py`.** After the build, a describer reads and runs the delivered code (read-only) and writes every business behaviour as a plain rule.
- **`start.handover` now begins with that sheet**, through `interview.confirm_sheet(..., missing=True)`. On the phone, numbered buttons mark the wrong rules. Each marked rule is said right and amended. Anything missing is added. The changes are remembered and go to one fix round on the same branch.
- If the sheet cannot be written, the old "looks right?" hand-over runs unchanged. `HIVE_CODE_SHEET=0` turns it off.
- Tests: the code-sheet hand-over (mark, amend, fix round; accept whole, no fix round) and `confirm_sheet` with "missing".

## Limits

- One run per team, one rule set, synthetic owner who knows his rules and reads carefully. This is the mechanism's ceiling.
- The owner and describer are the same model family as the builders. A describer that misreads the code would show the owner a wrong "what it does now". Here the owner corrected every such rule against his policy, not against the code.
- C's builders started fresh from the corrected sheet. In the product the sheet drives a fix round on the existing build instead. That path is implemented but not measured here.

## Files

As in Gate 41: `prompts/` (including the describer brief), `referee/` (`code_sheet.py`, analysis, unsealed oracle), `results/` (summary, analysis, probes, costs, sheets D and C, the review transcript, the interview, judge labels), `swarms/`, `logs/`.
