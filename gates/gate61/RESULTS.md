# Gate 61 results: the flight log, Oct 30 2026

**Question** (from the user: "Run the tests as required", after the proposal "a flight log that grows"). Outcomes an owner confirmed can be kept as tests, so the next build cannot break them. Does that matter? In follow-on work that rewrites the old code, how much confirmed behaviour do builders break without such a log, and does the log stop it?

**Answer.**
- **Nothing broke, with or without the log. The kill rule fired.**
- Six teams of 2 builders moved the ten functions from three files into one module, with shared helpers for input and rounding, and deleted the old files. Every team kept all 700 hidden calls right, the same as before the clean-up.

| Team | Flight log | Hidden calls right after build 2 | Build 1's right calls broken | `invoice_total` (60 calls) | Clean-up done |
| --- | --- | --- | --- | --- | --- |
| N1, N2, N3 | no | 700/700 each | 0 | 60/60 each | yes |
| T1, T2, T3 | 50 confirmed outcomes | 700/700 each | 0 | 60/60 each | yes |

- **Builders kept behaviour because they were told to.** The prompt said what the functions do now is what the business wants, and the clean-up must not change it. Every team consolidated real code: 215–229 lines in one module, with shared helpers such as half-up rounding and exact fractions. None changed an outcome.
- **At this scale, a confirmed decision is safe in the code itself, as long as the next task says to keep behaviour.** The log adds nothing to survival here.
- **What the log could still be worth is untested:**
  1. **Asking less on later builds.** The code sheet and spot checks would only cover behaviour the log does not already pin down.
  2. **A later task that pulls against an old decision.** For example, "accept amounts as text" against a confirmed "text gives no fee".

## Setup

- **Build 1:** Gate 55's CC build (a careful owner's review; 100% on Gate 55's hidden suite), here 700/700 on a new hidden suite (seed 61200000). Its ten functions sat in three files by three builders.
- **The flight log:** Gate 58's spotter wrote 50 concrete cases from build 1 (5 per function, with table setup for the aggregate). All 50 matched the policy, the referee's stand-in for a careful owner confirming them. They became tests in `tests/visible/` (ids `<function>_fNN`), which the landing guard checks.
- **Build 2** (`prompts/prompt_refactor.md`): the clean-up, plus a new `invoice_total` (bulk price plus the late fee on it).
- **Teams:** six teams of 2 builders, run 6 at a time (N1, T1, T2, N2, N3, T3). N teams had the existing suite; T teams also had the flight log and one README line about it.
- **Timing and cost:** every builder finished within 4.4 minutes; builders $2.58, spotter $0.29.
- Predictions pushed before the run (`2b02ecd`).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| F1 | An N team breaks ≥ 2% of build 1's right calls | **Failed:** 0% in all three |
| F2 | T's broke share is at most half of N's | **Failed:** 0 vs 0 |
| F3 | T hidden ≥ N + 2 points | **Failed:** 100 vs 100 |
| F4 | All 6 teams finish the clean-up | **Held** |
| Ship | F2 and F3 | **Did not fire** |
| Kill | N breaks < 1% | **Fired** |

## Disclosed: a referee bug in the secondary measure

- **The bug:** one of the two `invoice_total` example tests in the starting repos was written with Python's `None` where SQL needs `NULL` (`INVOICE_TOTAL(2000, 60, None)`). The same mistake was in the referee's 60 `invoice_total` calls.
- **Effect on the first scoring:** N teams 52/60 and T teams 60/60. All 8 misses were calls with a missing value, where N engines rejected the bare word `None`.
- **Rescored with `NULL`:** all six teams 60/60.
- Builders on N1 and N3 reported the bad example as failing. Some T builds happened to read the bare word as NULL. That difference comes from the bug, not the log.
- `invoice_total` was not a registered measure. The registered measures (hidden calls on the old functions) were unaffected.

## What it means

1. **No product change.** Hive already keeps the owner's rulings in text (`hive rules`) and builders keep behaviour when asked. Executable tests from confirmed outcomes are not needed to stop regressions in a clean-up of this size.
2. **The open value of a flight log is fewer questions on the next build** (Gate 61 did not measure it). The code sheet already drops rules that repeat his earlier rulings (`codesheet.split_known`).

## Limits

- One clean-up on one small codebase. Builders were told plainly that behaviour must not change.
- The log's confirmations came from the oracle, not a person.
- A task that conflicts with an old decision was not tried.

## Files

`prompts/`: the refactor prompt, the spotter brief and the predictions.

`referee/`: `run61.py` and `analyze.py`.

`results/`:
- `results.json`, with the rescored `invoice_total` and the first score kept as `invoice_right_harness_bug`;
- the flight log;
- probes, agents and the run log.
