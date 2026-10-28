# Gate 29 predictions, registered before the run (Oct 28 2026)

**Question.** Hive now keeps the owner's rulings across builds (`hive/memory.py`). **Do kept rulings actually carry into a new, related feature, so the builders follow the owner's earlier decisions without being asked again?** If not, memory is a list nobody reads.

**Design.**
- **Codebase.** The private, secret-checked copy of a real company's Node.js backend (Company X), on a base without the trial's feature. The company's repository is never pushed to.
- **Rulings.** The 15 the founder gave in the trial's phone review (same day): 4 changes and 11 confirmations, kept by `hive/memory.py`. They stay private.
- **Feature.** A new, related, unbuilt piece of the company's analytics: a pure library that summarises one campaign's creators (a combined engagement rate, total reach, followers per platform), with a fixed interface. Several of the founder's rulings bear on it. The goal does not state them.
- **Hidden cases.** Before the run, the experimenter wrote 5 cases. Each applies one of the founder's rulings to the new feature, using his recorded words. A private reference passes all 5. The cases are kept out of the container until scoring.
- **Arm M (memory).** `hive run`, 4 workers, no questions, assumptions recorded. The goal carries the standing rulings exactly as `hive start` adds them.
- **Arm N (no memory).** The same, without the rulings.
- Both arms run at the same time on the same base.

| # | Prediction |
| --- | --- |
| M1 | Arm M passes ≥ 4 of the 5 hidden cases |
| M2 | Arm N passes ≤ 2 of the 5 |
| M3 | All 384 existing tests pass in both arms |
| M4 | Arm M records fewer business assumptions than arm N (settled matters need no assumption) |
| M5 | No secret-like file committed; no breaking commit left broken, in either arm |

Kill: **arm M passes no more hidden cases than arm N.** Kept rulings do not carry into related work.

**Honest prior.** M1 about 70%. M2 about 60%: in the trial, builders without the rulings chose the opposite default on 4 of these points, but a different feature may lead them elsewhere. M4 about 60%.

**Limits known in advance.**
- The experimenter wrote the cases from the founder's rulings, and the rulings were mostly the founder accepting Hive's suggestions.
- One feature, one run per arm.
- The cases test whether rulings carry over, not whether they are right.

**Cost.** About $5 at list price. No owner time.
