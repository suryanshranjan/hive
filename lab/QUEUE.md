# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Where we left off (Oct 28 2026, after Gate 28)

- Hive v1 M1–M5 done. `hive start` added: type `hive`, describe the goal, and it does the rest (tests found, questions inline, assumption review, fix round, result as a branch). Tested with stand-in builders only (`tests/test_start.sh`).
- Gate 27: live questions tied with no questions on the founder's head-only rules (19/24 each). Gate 28: tied again (14/15 each). The builders' defaults already matched the founder, so the assumption review had no room, and the founder was away (proxy review, disclosed).
- **If this session is on the phone or the web (no laptop):** the company's code copy, the container and every private case live only on the laptop. Do **not** try to run a company gate, and never put the founder's answers or cases in this repo. Do Gate 29 step 1 only:
  1. Ask the founder, in plain words: "What do new people at your company usually get wrong about deals, terms or matching? List as many as come to mind, one line each."
  2. For each item, ask for one concrete situation and his verdict (what should happen, and what a newcomer would wrongly do).
  3. Save everything to a **private Notion page** titled "Hive Gate 29 private cases (do not share)", not to GitHub. Commit nothing about the cases.
  4. Update "Where we left off" here to say the Notion page exists and how many cases it has, then push.
  The laptop session then turns them into hidden tests, registers predictions and runs the gate.
- Trial: the first real `hive start --overnight` run on the company backend copy worked unattended (419/419 tests, 384 kept, 5 min, $2.49). 15 business assumptions are waiting for the founder: in the container, `cd /home/node/bn && PYTHONPATH=/tmp/hivepkg python3 -m hive morning`. Next tool step: rank assumptions by impact; consider a phone channel for questions and morning reviews (ideas from OpenClaw: chat channel, heartbeat, a file of owner rulings kept across builds).
- Next (Gate 29, needs the founder): **cases where the owner is surprising.** First ask him what new people usually get wrong about deals, terms and matching. Build 10 to 15 cases there, then rerun questions vs ranked assumption review (business defaults only, at most about 10 items), with the founder reviewing blind. Also: the first real `hive start` run on a real feature.

## Needs the user

### A person answering live
- Every answer so far came from encoded rules. Have the founder answer builder questions in real time on a small gate; measure consistency with their own rules and answer time (Gate 7's Q2 and Q3, never tested).

### G19 (folded into Gate 20): the company's documents
- The company's policy pages (Notion was unavailable on Oct 27: the connector did not authorize in this session) as the handbook; the confirmed rules answer.
- Publish only anonymized aggregate numbers, as in Gate 7.

## Running on a laptop (Docker)

Workers run shell commands, so run them in a container. Image: `node:22-bookworm` plus `python3 sqlite3 git` and `npm i -g @anthropic-ai/claude-code`, run as user `node`. Mount the repo read-write at `/host/hive` and `~/.claude/.credentials.json` read-only; copy the credentials into the container's `~/.claude/`; work in a fresh clone inside the container (a Windows checkout has CRLF line endings), with `origin` pointed at GitHub. Copy results back out and push from the host.

## Needs design first (write the config and predictions, push them, then run)

### G9: intent interface v1 vs free asking
- Arm A: free asking, 30 questions.
- Arm B: the interface from Gates 4 to 8. The spec lists each function's allowed input values (taken from the rule-giver's docs), questions spread at about 2 per function before any gets a third (Gate 11; blocks of 3 lost), one thing changes per question, and answers become tests.
- Needs: a "spec with allowed values" option in `lab/new_intent_gate.py` (one seed per arm), and the answers-as-tests step from Gate 7.

### Repeats
- Every gate is one run per team. The cheapest strengthening is a repeat of Gate 11 on a new rule-giver.

## Rules learned from Gates 8 and 11
- Check the referee's SQLite version against stored visible answers before generating a hidden suite (Gate 10).
- Workers often skip `export HIVE_LOG`; count claims and landings from git history instead (Gate 10).
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
