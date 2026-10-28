# Trial: the first real `hive start` run, overnight mode (registered before the run, Oct 28 2026)

**What this is.** A product check, not an intent experiment. `hive start` (Hive's one-command flow) has run only with stand-in builders. This trial runs it for real, unattended, on the private, secret-checked copy of a real company's Node.js backend (Company X). The company's repository is never pushed to.

**Feature.** An unbuilt piece of the company's analytics roadmap: a pure library that combines campaign metrics the way the spec requires. Rates are summed by numerator and denominator, never averaged. Division by zero is "not available". Metrics of different kinds are never mixed, and followers stay separate per platform. The goal quotes the spec's aggregation rules; anything else is left to the builders, who record their assumptions for the owner's morning review.

**How it runs.**
- `hive start --overnight --workers 4` with the goal given as a file, and nobody at the keyboard.
- The settings are whatever `hive start` works out on its own from the repository.
- No hidden tests: this checks the product flow, not intent.

| # | Prediction |
| --- | --- |
| T1 | The run completes unattended: no prompt blocks it, and the result arrives as a `hive/...` branch |
| T2 | All 384 existing tests pass on the result, and `hive start`'s own check reports none broken |
| T3 | Every builder exits cleanly, with no API errors |
| T4 | 3 to 12 **business** assumptions reach the owner's list, with technical choices filtered out (Gate 28 had 27 mixed items) |
| T5 | Under $6 and under 30 minutes |
| T6 | No secret-like file or artifact is committed |

**Failure means:** the one-command flow is not yet ready for a first-time user on a real codebase.
