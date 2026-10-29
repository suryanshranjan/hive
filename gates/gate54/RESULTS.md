# Gate 54 results: a bigger flight, with a real swarm, Oct 30 2026

**Question.** Fly `hive start`, as shipped, on a three-part goal so that a real swarm runs through the product: the law sizing the team, the interview, several builders sharing `shop/`, a live question to the owner, and one code sheet across areas. What breaks, and what does the owner get?

**Answer.**
- **First launch: a real product fault, now fixed.** A builder asked the owner a live question, and the keyboard input was closed. Hive's question loop took the closed input for "come back later" and showed the same question **173 times** in 9 minutes, while the builder waited up to 30 minutes. Fix (`hive/owner.py`):
  - a closed input is told apart from an empty line;
  - Hive says once that no one can answer;
  - builders are told to decide and record the assumption.

  The flight's harness now also answers prompts that read the keyboard directly. The launch was stopped and rerun from scratch; see `aborted_run/NOTE.md`.
- **The rerun flew cleanly:**
  - The law put **3 builders** on the job's 3 parts.
  - The interview turned the owner's answers into 10 confirmed rules.
  - A builder's live question (does the 50-rupee minimum apply to the half refund?) reached the owner and came back in one answer.
  - The build passed **26 of 27** hidden acceptance tests.
  - The code sheet showed the one remaining fault: negative days were treated as "not delivered", where his policy says day 0. The owner marked it, one fix round fixed it, and **27 of 27** passed after the hand-over.
  - Goal to branch took 7.4 minutes, with $0.50 of builders and 30 owner prompts.

## Predictions scored (`prompts/PREDICTIONS.md`, `e292fba`)

| # | Prediction | Result |
| --- | --- | --- |
| R1 | The law puts 3 builders on it | **Held** |
| R2 | End to end, no crash, one branch | **Held on the rerun.** The first launch hung on the closed-input fault; disclosed and fixed |
| R3 | ≥ 24 of 27 after the hand-over | **Held:** 27 |
| R4 | The hand-over does not make it worse | **Held:** 26 → 27 |
| R5 | At most 45 owner prompts | **Held:** 30 |
| R6 | Builder cost at most $3 | **Held:** $0.50 (Hive's own model calls not metered; the synthetic owner cost $1.95) |

## What the three flights show (Gates 52–54)

| Flight | Builders | Hidden before hand-over | After | Minutes | Builder cost | Owner prompts | Faults found |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 52 (one function) | 8 → 4 | 22/22 | 22/22 | 5.3 | $0.56 | 20 (+20 unanswerable) | two reviews; team size |
| 53 (same, fixed) | 1 | 22/22 | 22/22 | 5.0 | $0.24 | 25 | wording; a repeated list. The sheet caught 2 bugs the hidden tests missed |
| 54 (three parts) | 3 | 26/27 | **27/27** | 7.4 | $0.50 | 30 | closed input re-asked forever (first launch) |

**Established for a synthetic owner who knows his policy:** Hive delivers his rules end to end on small features. The code-sheet hand-over found and fixed what the build got wrong in 2 of 3 flights, and made nothing worse in any. Whether a person reads the sheet as carefully is Gate 45's question.

## Turned into the product

- `hive/owner.py`: a closed input no longer loops; builders are told to decide and record what they assumed (test in `tests/test_owner.sh`).
- Earlier this night, from Gates 52–53: team size by the job's parts; the code sheet replaces the one-by-one assumption review; one-builder wording; no repeated list after the sheet.

## Limits

- One flight per configuration, small features, a synthetic owner.
- Hive's own model calls (interview, describer, plain words) are still not counted in the cost it reports.

## Files

`prompts/` (owner brief, predictions), `referee/flight3.py` (Gate 52's driver), `aborted_run/`, `results/`:
- the policy and the 27 hidden tests, published now that the run is scored (synthetic);
- the flight summary, full terminal and the owner's replies;
- the project with the delivered branch.
