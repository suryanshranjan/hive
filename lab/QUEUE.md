# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Where we left off (Oct 27 2026, after Gate 12)

- Gates 0 to 8, 11 and 12 are done and written up (G9 and G10 are still cards). Gate 7 used a real company's rules, which stay private (never commit them).
- Gate 12 (`gate12/RESULTS.md`): with 1 to 4 hidden decisions per function, more decisions make each question weaker (D1 held), but a floor of 21% of errors was never fixed by any team, even with 4 questions per function. Every stuck error was a decision no builder thought to probe (caps, extremes, alternative formats, holidays). The bottleneck is where questions point.
- Next: G13, the owner's decision tour against builder questions (needs a per-arm seed repo in `run_gate.py`).

## Running on a laptop (Docker)

Workers run shell commands, so run them in a container. Image: `node:22-bookworm` plus `python3 sqlite3 git` and `npm i -g @anthropic-ai/claude-code`, run as user `node`. Mount the repo read-write at `/host/hive` and `~/.claude/.credentials.json` read-only; copy the credentials into the container's `~/.claude/`; work in a fresh clone inside the container (a Windows checkout has CRLF line endings), with `origin` pointed at GitHub. Copy results back out and push from the host.

## Needs design first (write the config and predictions, push them, then run)

### G13: decision tour vs builder questions
- **Why:** Gate 12's floor is decisions builders cannot imagine. The owner knows where they are.
- **Design:** rule-giver as in Gate 12, plus `DECISION_EXAMPLES` (one argument tuple per decision, not in TYPICAL or EDGE). Arms: N0; **T** (tour as visible tests, no questions); **Q** (team budget of 17 questions, about the same 50 answered values); **TQ** (tour plus 17 questions).
- **Needs:** per-arm starting repos (the tour added as visible tests for T and TQ only).
- **Predictions to register:** T fixes ≥ 1.3× Q's errors; TQ ≥ 0.80 of N0's edge errors; T fixes ≥ half of the errors Q leaves.

### G9: intent interface v1 vs free asking
- Arm A: free asking, 30 questions.
- Arm B: the interface from Gates 4 to 8. The spec lists each function's allowed input values (taken from the rule-giver's docs), questions spread at about 2 per function before any gets a third (Gate 11; blocks of 3 lost), one thing changes per question, and answers become tests.
- Needs: a "spec with allowed values" option in `lab/new_intent_gate.py` (one seed per arm), and the answers-as-tests step from Gate 7.

### G10: largest-first claiming at 12 and 20 workers
- Needs: `claim.py` to rank failing categories by size (failing-test count), and a scale config on `gate3/seed_scale.bundle` with `gate3/prompts/prompt_scale.md`.
- Prediction to register first: 12 workers finish under 7.0 minutes.

### Repeats
- Every gate is one run per team. The cheapest strengthening is a repeat of Gate 11 on a new rule-giver.

## Rules learned from Gates 8 and 11
- A law fitted on two gates can fail on the third: keep one-parameter fits labelled as models until a registered prediction from them holds.
- Matched pairs let one run measure a question's marginal value within the same functions; prefer them to level-by-level randomization.
- On a 429 usage limit, refresh the container's credentials from the host and rerun from scratch.
- Randomize allowances within strata of headroom (run N0 first), and report gains as the share of errors fixed, not raw points.
- Write a pre-flight power note before scoring; R2-style ordering predictions are weak at 5 functions per level.
- Reported worker tokens include cache reads; quote cost in dollars.

## Rules for every run
- Register predictions and push them **before** launching. `run_gate.py` refuses to start otherwise.
- Never commit hidden suites, or private rules of a run that has not been scored.
- Never commit anything about real companies (Gate 7's company stays anonymous).
- A run that dies midway is rerun from scratch; seeds make it reproducible apart from the new rules.
