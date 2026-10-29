# Gate 46, first launch: aborted (lab error), Oct 29 2026

The first `seed_deep.bundle` was wrong. Its commit recorded deleting the old engine (`git rm minisql`), but the
221-line skeleton copied in its place was never `git add`ed. So the project had **no `minisql/` at all**: `run_tests.py`
failed on import, against a prompt that said "9 pass, the engine is a 221-line skeleton".

What happened before the run was stopped (14:01 to 14:12):
- **F1 (7 flat workers):** every worker noticed the missing package within 20–30 seconds, claimed nothing, and stopped
  to ask: "you need to choose: rebuild from scratch or restore an older version" ($1.6 in all).
- **H1 (lead + 6):** the lead saw the same gap and made "land a skeleton" the first job in `BRAIN.md`; worker 1 landed
  one, and the team then built the **entire engine from nothing to 1,340/1,340 visible** in about 9 minutes (lead:
  plan after 45 s, 2 updates, $0.26).
- H2 had just started when the run was stopped. Nothing from this launch is scored.

Unplanned observation (one team each, prompts that did not match the repo; not evidence for the registered
question): flat builders treated a contradiction between their brief and the repository as a reason to stop and ask,
while a lead with a plan turned it into the first task. The seed was rebuilt (skeleton committed, 9/1,340 verified
from a fresh clone), and the gate reran from scratch.
