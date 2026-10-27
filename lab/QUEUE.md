# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Where we left off (Oct 27 2026, after Gate 8)

- Gates 0 to 8 are done and written up. Gate 7 used a real company's rules, which stay private (never commit them).
- Gate 8 ran on a Windows laptop inside Docker (about 7 minutes, $6.0 at list price). Results: `gate8/RESULTS.md`. Headline: R3 failed and its kill fired. Gate 6's weak first question was a headroom imbalance, and one law (each answer fixes about half the remaining edge errors, p ≈ 0.55) fits both gates. "Ask in blocks of 3" is withdrawn.
- Nothing is ready to run. The next card (G11) needs its config and predictions first.

## Running on a laptop (Docker)

Workers run shell commands, so run them in a container. Image: `node:22-bookworm` plus `python3 sqlite3 git` and `npm i -g @anthropic-ai/claude-code`, run as user `node`. Mount the repo read-write at `/host/hive` and `~/.claude/.credentials.json` read-only; copy the credentials into the container's `~/.claude/`; work in a fresh clone inside the container (a Windows checkout has CRLF line endings), with `origin` pointed at GitHub. Copy results back out and push from the host.

## Needs design first (write the config and predictions, push them, then run)

### G11: one-per-function vs blocks of 3, stratified by headroom
- **Why:** the Gate 8 law predicts that one question per function before any second fixes about 1.5× the errors of blocks of 3. This is the test that could kill the law.
- **Design:** fresh rule-giver and seeds. Stage 1: run N0 alone and measure each function's edge errors on the hidden suite. Stage 2: two arms with 30 questions each. **S** gets one question per function plus a second on 10 functions; **B** gets 3 questions on 10 functions. Pick the 10 functions per arm to match on N0 headroom.
- **Prediction to register:** S fixes ≥ 1.3× the edge errors B fixes. **Kill:** B fixes as many or more.
- **Needs:** `run_gate.py` to take a precomputed allowance per arm (it already takes `allowance.counts`; add explicit per-function lists), and a stage-1 mode that stops after scoring N0.

### G9: intent interface v1 vs free asking
- Arm A: free asking, 30 questions.
- Arm B: the interface from Gates 4 to 8. The spec lists each function's allowed input values (taken from the rule-giver's docs), every function gets a first question before any gets a second (Gate 8; blocks of 3 withdrawn), one thing changes per question, and answers become tests.
- Needs: a "spec with allowed values" option in `lab/new_intent_gate.py` (one seed per arm), and the answers-as-tests step from Gate 7.

### G10: largest-first claiming at 12 and 20 workers
- Needs: `claim.py` to rank failing categories by size (failing-test count), and a scale config on `gate3/seed_scale.bundle` with `gate3/prompts/prompt_scale.md`.
- Prediction to register first: 12 workers finish under 7.0 minutes.

### Repeats
- Every gate is one run per team. The cheapest strengthening is to rerun G8 with a new rule-giver and a new seed, with allowances stratified by N0 headroom; it gives a third estimate of p.

## Rules learned from Gate 8
- Randomize allowances within strata of headroom (run N0 first), and report gains as the share of errors fixed, not raw points.
- Write a pre-flight power note before scoring; R2-style ordering predictions are weak at 5 functions per level.
- Reported worker tokens include cache reads; quote cost in dollars.

## Rules for every run
- Register predictions and push them **before** launching. `run_gate.py` refuses to start otherwise.
- Never commit hidden suites, or private rules of a run that has not been scored.
- Never commit anything about real companies (Gate 7's company stays anonymous).
- A run that dies midway is rerun from scratch; seeds make it reproducible apart from the new rules.
