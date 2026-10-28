# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Where we left off (Oct 28 2026, after Gate 37)

- **Done:** Gate 36 scored and written up (`gates/gate36/RESULTS.md`). Kill fired: interview first, with questions written from the description alone, gave 2/7 surprising cases in both arms. Coverage was 4/9, and on both covered cases the founder's interview answer contradicted his hidden-set verdict.
- **Tool**, all tests passing:
  - `hive` (start, overnight, morning, interview first).
  - Telegram: formatted cards with progress bars, voice notes via local Whisper, questions, reviews, status, undo, change of mind via `hive listen`, "build: ...".
  - Memory of rulings, contradiction checks (now including interview answers), as-built confirmation.
  - **Picking up again:** interview answers are saved and resumed; taps on old buttons are answered; a builder stopped by a usage limit or an expired login resumes, and the owner is told.
  - `hive doctor`, `pip install`, `hive cloud` (tested on a real EC2 instance).
- **Gate 37 pilot done** (`gates/gate37/PILOT_RESULTS.md`, no founder time): an interview written from the code's decisions covered 7 of 9 of Gate 36's surprising situations, against 3 from the description. Hive now asks about every decision the code takes, up to 20.
- **Done: Gate 37** (`gates/gate37/RESULTS.md`), kill fired.
  - Coverage is solved: 6 of 6 from the code's decisions.
  - The builders followed his answers.
  - But his answers to two framings of a decision agree only 1 of 8 (same session) and 3 of 6 (a day apart), so the score did not move.
  - The interview was redundant; fixed in `f5fccc1`.
- **Next: Gate 38, decide once, as a rule** (`BRAIN.md` §9).
  - Build the rule sheet first: after the interview, Hive shows one general rule per decision, flags disagreeing answers, and the owner confirms or edits each.
  - Then register predictions and run it over two days with the founder (about 15 minutes).
- **Private:** Gate 37's material is in `hive_private\g37priv` and `/home/node/g37` in the container.
- **Private material:** `D:\Suryansh\Programming\hive_private\` (`g36priv`: hidden tests, reference, scripts) and `/home/node/g3x` in the container.

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
