# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Where we left off (Oct 27 2026, 16:30 IST)

- Gates 0 to 7 are done and written up. Gate 7 used a real company's rules, which stay private (never commit them).
- `lab/` now runs a whole intent gate in one command. It was tested end to end with stub workers and one real headless worker.
- Gate 8's predictions are registered (`gate8/prompts/PREDICTIONS.md`). Nothing has run yet.

## Ready

### G8: the intent curve, replicated, with the 2-question point
- **Run:** `python3 lab/run_gate.py lab/experiments/g8_curve.json` (add `--max-parallel 3` on small machines).
- **Cost:** about 0.8M tokens (1 rule-giver and 6 builders); about 20 to 30 minutes.
- **Afterwards:**
  - Write `gate8/RESULTS.md` from `runs/g8/summary.md` and score R1 to R5.
  - Copy `private/g8/oracle.py` to `gate8/referee/` (the run is scored, so the rules may be published; they are synthetic).
  - Update BRAIN.md and this file, then push.

## Needs design first (write the config and predictions, push them, then run)

### G9: intent interface v1 vs free asking
- Arm A: free asking, 30 questions.
- Arm B: the interface from Gates 4 to 7. The spec lists each function's allowed input values (taken from the rule-giver's docs), questions come in blocks of about 3 per function, one thing changes per question, and answers become tests.
- Needs: a "spec with allowed values" option in `lab/new_intent_gate.py` (one seed per arm), and the answers-as-tests step from Gate 7.

### G10: largest-first claiming at 12 and 20 workers
- Needs: `claim.py` to rank failing categories by size (failing-test count), and a scale config on `gate3/seed_scale.bundle` with `gate3/prompts/prompt_scale.md`.
- Prediction to register first: 12 workers finish under 7.0 minutes.

### Repeats
- Every gate is one run per team. The cheapest strengthening is to rerun Gate 6's design (or G8) with a new rule-giver and a new seed.

## Rules for every run
- Register predictions and push them **before** launching. `run_gate.py` refuses to start otherwise.
- Never commit hidden suites, or private rules of a run that has not been scored.
- Never commit anything about real companies (Gate 7's company stays anonymous).
- A run that dies midway is rerun from scratch; seeds make it reproducible apart from the new rules.
