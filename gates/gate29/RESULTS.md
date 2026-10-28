# Gate 29 results: do the owner's kept rulings carry into a related feature? Oct 28 2026

Only aggregate numbers are published. The company (Company X), its spec, code, the founder's rulings and the cases stay private.

**Question.** With the founder's 15 rulings from the trial kept by Hive's memory, do builders follow them on a new, related feature, where builders without them would not?

**Answer: this gate could not tell, and the kill fired. The reason is the main finding.**
- **Both arms passed all 5 hidden cases.** The swarm without the rulings got them right too.
- **The founder's 4 changes were all Hive's own suggestions,** taken with one tap in the trial review. A ruling that matches what the model would suggest anyway is one a builder without memory reaches by itself. So these rulings could not separate the arms.
- **The fixed interface also pointed toward the rulings.** It had a count of creators included and an account identifier. This was flagged as a risk before the run, and it applied.
- **Memory still roughly halved the owner's review list:** 13 business assumptions with the rulings against 25 without. Settled matters needed no assumption, so the owner has about half as many decisions to review.

| Measure | Arm M (with the 15 rulings) | Arm N (without) |
| --- | --- | --- |
| Hidden cases (each applies one ruling) | **5 / 5** | **5 / 5** |
| Existing backend tests | 384 / 384 | 384 / 384 |
| All tests on the final branch | 428 / 428 | 423 / 423 |
| Business assumptions for the owner | **13** | **25** |
| Technical assumptions (engineers only) | 3 | 4 |
| Cost | $2.62 | $2.99 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| M1 | Arm M passes ≥ 4 of 5 | **Held:** 5 / 5 |
| M2 | Arm N passes ≤ 2 of 5 | **Failed:** 5 / 5 |
| M3 | 384 existing tests pass in both arms | **Held** |
| M4 | Arm M records fewer business assumptions than arm N | **Held:** 13 vs 25 |
| M5 | No secret-like file; no breaking commit left broken | **Held** |
| Kill | Arm M passes no more hidden cases than arm N | **Fired:** 5 vs 5 |

## What it means

1. **The same law, a third time.** An intent channel can only add value where the owner's rule differs from the builder's default:
   - Gate 27: questions tied with no questions.
   - Gate 28: the assumption review had no room.
   - Gate 29: memory tied with no memory.

   Each time, the owner's rules on the cases tested were ones a capable builder reaches anyway. The rulings here were literally the model's own suggestions, accepted by the owner. (Model, now with three consistent results.)
2. **What memory does give, measured:** about half as many decisions for the owner to review on related work. That is time, not correctness.
3. **What a fair test of memory needs:** rulings where the owner *rejected* Hive's suggestion or answered in his own words, and an interface that does not hint at them. That is the same requirement as Gate 30: cases where the owner is surprising.
4. **For the product:** suggestions plus one-tap acceptance make reviews fast, and they also make the owner's rulings converge on the model's defaults. That is useful when the defaults are good. But it is exactly where Hive adds least over a plain coding agent. Hive's edge is the owner's *disagreements*, so the review should make disagreeing as easy as agreeing.

## Limits

- One feature, one run per arm, five cases.
- The cases were written by the experimenter from the founder's rulings.
- The interface hinted at two of the rulings.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions |
| `RESULTS.md` | This file (aggregates only) |
