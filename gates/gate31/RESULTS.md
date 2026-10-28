# Gate 31 results: the new review on a fresh feature, Oct 28 2026

Only aggregate numbers are published. The company (Company X), its spec, code, situations and the founder's verdicts and choices stay private.

**Question.** With the review rebuilt after Gate 30, does the owner's input now carry his surprising rules into the code? The rebuilt review has the owner scan every decision in one line and mark the ones he would change, asks those openly first, ranks by likely disagreement and checks against his earlier rulings.

**Answer: the scan worked and the next step failed, so this gate did not test what it set out to.** The kill condition fired.
- **Coverage, the part Gate 30 got wrong, worked.** Builders recorded an assumption touching all **9** of the founder's surprising rules. Scanning the full list, he marked a matching decision for **8 of 9** (C1 held, against 3 of 6 in Gate 30).
- **Then no change came out.** He marked 22 of the 29 decisions, and for each of the 22 he tapped **"Keep it as is"**, in 2 to 12 seconds. With 0 corrections there was no fix round, so arm R is arm N: **3 of 9** surprising cases in both.
- The likely cause is the review's design, not the founder:
  - the list's instruction ("tap any you'd do differently") read as "tap the ones to look at";
  - each marked decision then opened with "Keep it as is" as its first button.

  He chose to record the gate as it stands and fix the flow, rather than re-review the same build.

| Measure | Arm N (no owner) | Arm R (after his review) |
| --- | --- | --- |
| **Surprising cases** | **3 / 9** | **3 / 9** (no changes were made) |
| Ordinary cases | 3 / 3 | 3 / 3 |
| Existing backend tests | 384 / 384 | 384 / 384 |
| Cost | $2.43 (build) | no fix round |

| The review | |
| --- | --- |
| Business decisions listed | 29 (plus 4 technical, for engineers) |
| Marked by the founder | 22 |
| Changed / kept among the marked | 0 / 22 (2 to 12 seconds each) |
| Surprising rules with a matching recorded assumption | 9 of 9 |
| …where he marked a matching decision | **8 of 9** |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| S1 | On surprising cases, R beats N by ≥ 30 points | **Failed:** 0 (no corrections were made) |
| C1 | He marks a matching decision for ≥ 80% of the surprising rules recorded | **Held:** 8 of 9 (89%) |
| S2 | Ordinary cases ≥ 75% in both arms | **Held:** 3 / 3 |
| S3 | Existing backend tests pass in both arms | **Held** |
| S4 | Review under 10 minutes | **Held** |
| S5 | No secret-like file; no breaking commit left broken | **Held** |
| Kill | R beats N by < 10 points | **Fired:** 0 |

## What it means

1. **Scanning the whole list fixes coverage.** Gate 30's ranking showed the founder 3 of his 6 surprising rules. Gate 31's one-line list let him find 8 of 9 himself. The bottleneck has moved from finding the decisions to getting the owner's answer on them.
2. **The answering step needs to reflect that he marked it.** If the owner marks a decision as one he would change, the next screen must ask for *his way*, not open with "Keep it as is". A fast run of "keep" on decisions he marked is a signal to check, not to accept.
3. **Changes to the tool from this gate:**
   - A marked decision now asks "What would you do instead?", with "Actually, keep it as is" as the last, separate button.
   - Three quick keeps of marked decisions in a row prompt "Did you mean to?" and offer to go back.
   - The list says to tap only what the owner would *change*, and that the rest stays as it is.
4. **Next:** Gate 32, the same design on another fresh feature, with this flow.

## Limits

- One founder, one feature, one build.
- The founder did not describe what he intended on the review.
- The cause above is an inference from the timings and the flow.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions and the pre-build amendment |
| `RESULTS.md` | This file (aggregates only) |
