# Gate 89 results: no business decisions, no interview, Nov 2 2026

**Question.** Gate 86: on Django bug reports, Hive's owner interview invented a shop to ask about. With the planner told that a technical fix has no business decisions, and no interview without them, does the reporter's load fall, at no loss?

**Answer.**
- **The interview is gone where it should be, and nowhere else.**
  - On all 10 Django issues the planner found 0 business decisions (3 of 3 calls each). Hive said "This goal has no business decisions for you to rule on" and asked nothing first (K5).
  - On two business goals the planner still found 14 to 19 decisions (K4).
  - Accuracy held: 7 of 10, against 8 (K2; the one loss, `13513`, was the issue only Hive's flow had recovered in Gate 86).
- **But the load did not fall:** a median of 21.5 prompts against 23.5, and the cost the same ($19.02 against $19.72). The claim did not fire.
  - The prompts came from the review after the build, which Hive runs whenever builders asked fewer than 3 questions: a code sheet of 20-odd rules about URL reversing or ORM internals, then 9 to 24 spot checks, put to someone who reported a bug.
  - The registered rule for this case: "the remaining prompts come from the review after the build. That is the next target."

| | Resolved | Reporter prompts (median) | Interview | Cost, all 10 |
| --- | --- | --- | --- | --- |
| Gate 86 S (interview on) | 8 of 10 | 23.5 | invented a business on all 10 | $19.72 |
| **S2 (no business decisions, no interview)** | 7 of 10 | 21.5 | none on 10 of 10 | $19.02 |
| Gate 86 F (one builder, full issue) | 8 of 10 | 0 | – | $1.34 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| K1 | S2's median reporter prompts ≤ 8 | **Failed:** 21.5 (the review) |
| K2 | S2 resolves ≥ 7 of 10 | **Held:** 7 |
| K3 | S2's cost ≤ 0.4× S's | **Failed:** 0.96× |
| K4 | ≥ 5 decisions on both business goals, every call | **Held:** 14–19 |
| K5 | No interview on ≥ 8 of 10 issues | **Held:** 10 |
| Claim | K1–K4 | **Did not fire** |

## Disclosed

- **The change was merged to main before this gate ran.** It rode with Gate 90's fix on branch `dev90`, so Gate 90's flights used it. On Tiny Shop's business goal the interview ran as before (K4 here, and Gate 90's flights).
- **This gate first ran during the disk-full at 05:59,** and all 10 runs failed at once. It was rerun in full; scored copies were deleted after each run to save space.

## What changes in Hive

- **The interview skip stays:** it removes questions that made no sense (K5), with no measured harm (K2, K4), though the claim as registered did not fire.
- **Next: no business decisions, no business review either.** A goal with no business decisions has nothing for an owner to rule on after the build either. Hive should deliver with its tests and the interface check, as one builder would.
  - On these issues one builder resolved 8 of 10 for $1.34. Hive's flow resolved 7 for $19.

## Files

`prompts/`, `referee/` (`run89.py`, `plan89.py`, `analyze.py`).

`results/S2_<issue>/`: the result, the reporter's terminal, and every prompt and reply.

`results/g89_plan.json` (the planner's decisions per goal), `results/analysis.txt`.
