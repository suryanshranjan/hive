# Hive's failures, labelled with MAST

Gap 7 of `docs/gap_plan.md`. MAST is the failure taxonomy for multi-agent LLM systems from Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (NeurIPS 2025; arXiv 2503.13657). It has 14 modes in 3 categories, built from 1,642 traces.

We use their words instead of inventing our own, so Hive's failures can be compared with what other systems fail at. The labels are given by hand, from each gate's own evidence. A failure can carry two labels.

| Gate | What went wrong | MAST mode(s) | Fixed by |
| --- | --- | --- | --- |
| 71 | Builders' questions to a slow owner were lost to their 2-minute command cutoff | FM-1.5 Unaware of termination conditions | Gate 72: a 90-s ask; the question stays with the owner |
| 73 | Hive asked every question up front and flooded the owner (65 questions, 64 min) | FM-1.3 Step repetition (design) | Not shipped |
| 76, 77 | Overnight builds missed decisions no builder thought to record | FM-2.2 Fail to ask for clarification | Open (the overnight split gave +0.7, not shipped) |
| 78, 80 | Free-text claims overlapped; 5.7 of 12 functions rebuilt by 2+ builders | FM-1.3 Step repetition; FM-1.2 Disobey role specification | Gate 80: areas named from the goal |
| 81 | One builder claimed every area; others idle | FM-1.2 Disobey role specification (a fair share was never stated) | Gate 81: an even share per claim |
| 81 | A builder whose claim was refused built and landed anyway | FM-2.5 Ignored other agent's input; FM-1.2 | Gate 81: `hive land` needs a lock |
| 82 | Landed areas looked free; two builders began rebuilding them | FM-1.3 Step repetition; FM-1.5 Unaware of termination conditions | Gate 82: landed areas shown, `--again` |
| 83 | An owner answer led a builder to change a result shape the goal had fixed; the review was skipped | FM-1.1 Disobey task specification; FM-3.2 No or incomplete verification | Gate 84: interface check when the review is skipped |
| 90 | A review correction made a builder add a `split` key to `refund()`'s stated result; the interface check ran only on the skip path | FM-1.1 Disobey task specification; FM-3.2 | Interface check before every delivery (shipped, `767d66d`) |
| 93 | "Only delivered orders" built as `delivered: bool = False` on Order, so every ordinary refund became 0 | FM-1.1; FM-3.2 | Open: the ordinary case first in the spot checks (to test) |
| 85 | "Already refunded" kept as module-level state, so later calls returned 0; the 32 spot checks missed it | FM-1.1 Disobey task specification; FM-3.2 No or incomplete verification | Open |

## What the pattern says

- **System design, MAST's largest category (FC1), is where most of Hive's failures were.** That matches MAST's finding: a better-designed system beats a better model.
  - The four claim-protocol faults (Gates 78–82) were all FC1 or FC2 mistakes in the coordination rules, not in the builders' skill.
  - Each was fixed by a rule in the tool, not a prompt. MAST reports that prompt-only fixes are unreliable.
- **Verification (FC3) is the open category.** Two failures in the last three gates were wrong code that the checks did not look for: a result shape (now checked) and state carried between calls (not yet).
  - MAST's ChatDev result fits: an objective, task-level verification step gave +15.6%, and shallow verifiers are not enough.
  - Next, a check of task-level properties every business function should have. Example: the same inputs give the same result, whatever was called before.
- **FM-2.2, failing to ask, appears only where nobody can be asked** (overnight). Live, Hive's builders ask (Gates 66–75).
