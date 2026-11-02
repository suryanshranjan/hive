# Gate 94 results: a technical goal gets one builder's treatment, Nov 2 2026

**Question.** Gate 89 removed the business interview from technical goals, but the reporter still answered about 21 prompts from the review after the build, at 14× one builder's cost. If a goal with no business decisions also skips the business review (tests and the interface check only), is Hive as good as one builder, at close to its cost?

**Answer.**
- **Yes. The claim fired.**
  - On Gate 86's 10 Django issues, Hive now resolved **8 of 10**, the same as one builder with the full issue.
  - It did so with a **median of 0 reporter prompts** (0–2: the fast/cheap question once, and two builder questions on two issues).
  - It cost **$3.64** for all 10, against $19.02 before (0.19×). One builder cost $1.34.
- **It resolved `django__django-15022`, which every other arm failed** (one builder, full issue or summary, and Hive's flow before). It lost `13513`, the issue the summary had made hard.
- **The law chose the builders by the work:** 1 builder on 7 issues, 2 on 3. Each issue took 1–3 minutes.
- **The interface check raised three false alarms, now fixed.** On bug reports it read names like "ExpressionWrapper", "QuerySet.alias" and "URL translation function" as functions the goal fixed, and sent a builder to "put them back".
  - The three builds still resolved, but each paid for a needless fix round.
  - The check now looks only at functions the goal places in a file and names as code (`hive/contract.py`, on branch `dev95`, unit-tested).

| Arm (10 Django issues) | Resolved | Reporter prompts (median) | Cost, all 10 |
| --- | --- | --- | --- |
| One builder, full issue (Gate 86 F) | 8 | 0 | $1.34 |
| One builder, summary only (Gate 86 N) | 7 | 0 | $1.23 |
| `hive start` before (Gate 86 S) | 8 | 23.5 | $19.72 |
| No interview (Gate 89 S2) | 7 | 21.5 | $19.02 |
| **No interview, no business review (S3)** | **8** | **0** | **$3.64** |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| T1 | Median reporter prompts ≤ 3 | **Held:** 0 |
| T2 | Resolves ≥ 7 of 10 | **Held:** 8 |
| T3 | Cost ≤ 0.35× S2's | **Held:** 0.19× |
| T4 | No delivery breaks a stated interface | **Held** (three false alarms, no broken delivery) |
| Claim | T1, T2 and T3 | **Fired** |

## What changes in Hive

- **The change stays on main** (merged before this gate). For a goal with no business decisions, Hive behaves like one careful builder: the law picks the builders, the guard and the interface check run, and the owner is asked nothing he has no rule about.
- **The interface check's false alarms are fixed** on `dev95` (merged with Gate 95).

## Limits

- 10 issues, one run each, from a repository the models know. The leftover cost over one builder ($3.64 against $1.34) is Hive's own steps: the part-naming call, the planner, the interface check.

## Files

`prompts/`, `referee/` (`run94.py`, `analyze.py`).

`results/S3_<issue>/`: the result, the terminal, and every prompt and reply. `results/analysis.txt`.
