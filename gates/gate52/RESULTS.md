# Gate 52 results: a flight test of the product, Oct 30 2026

**Question.** Fly Hive as shipped, `hive start` from goal to branch, once, with a synthetic owner answering every prompt from a private refund policy. What does one owner get end to end, and what breaks?

**Answer.**
- **It flew.** In 5.3 minutes it went from goal to delivered branch with no crash. The delivered `refund()` passed **22 of 22** hidden acceptance tests written from the owner's policy before the run. It passed them as built, and still after the hand-over. Builder cost was $0.56. The synthetic owner answered 20 prompts ($1.25, reported separately).
- **The owner's rules got in through the interview.** Hive asked 9 situations (2 skipped as settled by earlier answers). His "Not quite" on the 30-day rule was amended correctly to add damaged goods up to 90 days with shipping refunded. On the rule sheet he fixed one rule, the changed-mind refund, adding the 14/30-day halves, the 50-rupee minimum and negative days, in one correction. The built code follows every rule of his policy.
- **Three product findings:**
  1. **Two reviews where one does** (fixed). After the build, Hive put **20 assumptions** to the owner one by one, then showed the code sheet covering the same ground. In this run the 20 went unanswered: that review reads the keyboard directly, the harness could not type into it, and an empty input counts as "keep". **Fix:** when the code sheet can be written, it replaces the one-by-one assumption review ("Rather than going through them one by one, I'll show you everything the build does, as rules"). The assumptions stay on file for `hive morning`.
  2. **Team size before the interview** (noted). The law announced 8 builders, at "about 2.2× the cost", for a one-function job. After the interview it cut to 4 by the job's decisions. One builder did all the work in a minute; three found nothing to claim. This cost little here ($0.56 in all), but the law should count independent areas of work, not only decisions. On the queue.
  3. **The narration was honest and short.** The owner saw who landed what, the team size and why, and the speed-cost trade. No faults were found in the interview, the readings or the sheet.

## Predictions scored (registered in `prompts/PREDICTIONS.md`, `96d7866`)

| # | Prediction | Result |
| --- | --- | --- |
| P1 | Runs end to end and delivers a branch, no crash | **Held** |
| P2 | ≥ 20 of 22 hidden tests after the hand-over | **Held:** 22 of 22 |
| P3 | The hand-over does not make it worse | **Held:** 22 before, 22 after |
| P4 | The owner is asked at most 40 times | **Held, at the limit:** 20 prompts answered, plus 20 assumption prompts that read the keyboard directly and were kept unanswered (finding 1) |
| P5 | The build costs at most $10 | **Held:** $0.56 for the builders. The interview's and the code sheet's model calls are not metered by Hive; the synthetic owner cost $1.25 |

## Turned into the product (this commit)

- `hive/start.py`: when a build leaves assumptions and the code sheet can be written, the sheet replaces the one-by-one review. `handover(…, sheet=…)` reuses the sheet already written.
- `tests/test_start.sh`: a run with a describer that writes a sheet checks that the assumptions are covered by it and not reviewed one by one. All suites pass (`test_cloud.sh`'s 2 known failures aside).

## Limits

- One flight, one small feature, a synthetic owner who knows his policy.
- The builders' cost is what Hive records; its own model calls (interview, sheet) are not metered.

## Files

`demo/` (the project), `prompts/` (owner brief, predictions), `referee/flight.py`, `results/`:
- the policy and hidden tests, published now that the run is scored (synthetic);
- the flight summary and full terminal transcript;
- the owner's replies;
- the project with the delivered branch (`tinyshop.bundle`).
