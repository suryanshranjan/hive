# Gate 28 results: the assumption review, Oct 28 2026

Only aggregate numbers are published. The company (Company X), its spec, code, cases, verdicts, answers and the builders' assumptions stay private.

**Question.** In Gate 27, live questions did not carry the founder's unwritten rules. Builders never asked about defaults they felt sure of. If builders write down every default they apply and the founder corrects the wrong ones, are those rules recovered?

**Answer: this gate could not tell.**
- **On this feature, the builders' defaults already matched the founder.** Before any review, the swarm that could not ask passed **14 of 15** head-only cases. The swarm that asked the founder also passed 14 of 15. That triggered the ceiling rule registered before the run, so the main predictions (P1, P2 and the kill) are scored **no room**.
- **The founder could not do the review,** because he was away from power. The experimenter stood in, using only the reasons the founder wrote with his verdicts. The experimenter had also written the hidden tests, so the review was not blind. R-after's 17 of 17 is therefore **not evidence for the review**. It does show that a correction round on real code breaks nothing.
- **The clearest finding is about questions.** Arm Q's questions fixed one case and broke another, as described below.

## Setup

- **Codebase.** The same private, secret-checked copy of the company's Node.js backend, on the Gate 27 base. The company's repository was never pushed to.
- **Feature.** A pure library that decides whether an edit to signed collaboration terms needs both sides to accept again. The spec says only "any material edit"; what counts as material is left open.
- **Cases.** 17 edits to one signed deal, proposed by the experimenter, with verdicts from the founder: 15 need re-acceptance and 2 do not. Labelled before the run: 2 documented and 15 head-only. The cases were kept out of the container until scoring.
- **Arm Q:** 4 workers, the founder answering live. **Arm R:**
  1. 4 workers, no questions, recording their assumptions;
  2. a review of those assumptions;
  3. a 1-worker fix round.
- Predictions were pushed before the run (commits 8a43f4e, 46bcddf).

| Measure | Arm Q (asks the founder) | R-before (no questions) | R-after (review and fix) |
| --- | --- | --- | --- |
| All 17 cases | 16 / 17 | 16 / 17 | 17 / 17 (proxy review, not blind) |
| Documented | 2 / 2 | 2 / 2 | 2 / 2 |
| Head-only | 14 / 15 | 14 / 15 | 15 / 15 |
| Existing backend tests | 384 / 384 | 384 / 384 | 384 / 384 |
| All tests on the final branch | 420 / 420 | 422 / 422 | 427 / 427 |
| Questions or assumptions | 5 questions, all answered by the founder (39 to 90 s, median 80 s) | 27 assumptions recorded | 1 correction (proxy) |
| Commits | 15 | 9 | 13 (4 in the fix round) |
| Cost | $3.05 | $2.38 | +$0.90 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| P1 | R-after beats R-before by ≥ 20 points on head-only cases | **No room** (ceiling rule: R-before 93%). R-after reached 100%, but only through a proxy review that was not blind |
| P2 | R-after beats arm Q by ≥ 15 points on head-only cases | **No room** |
| P3 | Documented cases do not drop after the review | **Held:** 2/2 before and after |
| P4 | All 384 existing tests pass at the end of every phase | **Held** |
| P5 | The assumption list names the situation behind ≥ 70% of R-before's head-only misses | **Failed:** 0 of 1, judged before the review. The one miss was a spelling fix in the brief. No assumption named it; the nearest said a change of letter case counts as material |
| P6 | The founder's review takes under 15 minutes | **Not measured:** the founder was away; the review was by proxy |
| P7 | Arm Q within 10 points of R-before on head-only cases | **Held:** 93% vs 93% (replicates Gate 27's tie) |
| Kill | R-after beats R-before by < 10 points | **No room** |

## What it means

1. **Questions cut both ways.**
   - Arm Q asked about a spelling fix, so it got that case right, which R-before did not.
   - It also asked about a wording-only change to a barter item ("shoes" to "running shoes"), and the founder said that needs no re-acceptance. A builder then stretched this into "a renamed item never needs re-acceptance", so arm Q missed the case where the kit is swapped for a *different* product of the same value. The founder's verdict on that case was that the actual product matters.

   One answer fixed a case and the other broke one: a net gain of zero. This is Gate 4's failure (builders stretch rulings into rules), seen again with a real founder, despite the prompt's instruction not to.
2. **An unwritten rule only matters where it differs from the default.** Of 15 head-only cases, 14 matched what builders did without asking. Gate 27 found 6 of 10. Any intent channel (questions, examples, a review) can only add value on the cases that differ: 4 of 10 in Gate 27, 1 of 15 here. Choosing features and cases where the owner is *surprising* is now the bottleneck for measuring this (model).
3. **The assumption list was long, technical, and missed the one case that mattered.** 27 assumptions came from about 2 minutes of building. Many were about error handling that an owner cannot judge. The one real miss (a spelling fix) appeared only next to it, as "a change of letter case counts as material". A review of 27 items with one useful line in it is a poor use of a founder's time. If the review is to work, the list needs ranking and trimming.
4. **A correction round on real code is safe.** The fix round changed the rule, rewrote one existing test that asserted the overturned assumption, and kept all 384 original tests and every other new test passing.

## Changes to the tool from this gate

- `hive land <name> --continue` failed to parse, which a worker reported. Fixed.
- `corrections.md` now tells fix-round workers that a test asserting an overturned assumption must be changed to the owner's rule and named in the land message. The guard accepts an edited test that passes.

## Limits

- One run per arm, one feature, one founder.
- R-after's review was by the experimenter, who knew the cases.
- The ceiling left nothing for the review to recover.
- The case set was proposed by the experimenter. In both Gates 27 and 28, most of the founder's verdicts matched the obvious default.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Predictions and the pre-run amendment |
| `RESULTS.md` | This file (aggregates only) |
