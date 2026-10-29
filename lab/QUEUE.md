# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Where we left off (Oct 29 2026, afternoon, after Gate 38)

- **Gate 46 done** (asked for by the user): a lead with a shared BRAIN.md over 6 builders lost to 7 flat builders on a deep project (95% at 6.4 vs 5.3 min on average, cost 1.09×, same correctness). Hive stays flat. A Codex lead can be rerun with `gates/gate46/` on the user's machine.

- **Gate 38 is done, kill fired** (`gates/gate38/RESULTS.md`). The founder's 13 confirmed rules matched his next-day verdicts on 2 of 11 decisions (raw answers also 2 of 11). Builders followed the rules exactly: surprising 3/6 vs 0/6, ordinary 2/6 vs 5/6, a tie at 5/12. The hand-over (code sheet) is the main intent channel; the interview only seeds it.
- **Next: Gate 45, with the founder** (registered in `gates/gate45/prompts/PREDICTIONS.md`). Ready in the container:
  - N0 is built (4 builders); the code sheet is written (46 rules, `/home/node/g45/sheet_D.json`);
  - `/home/node/g45/review45.py` runs Hive's paged sheet on his phone (frozen Hive at `/tmp/hive45r`) and saves his corrected sheet C. Run it only when he is ready: nothing else may use his Telegram meanwhile.
  - Then day 2 (12 fresh situations, cold probe, blind judge), build I from goal + C, score, RESULTS.
- **Tool, this session (all suites pass):**
  - The real Codex works as Hive's builder (2 builders, 7.8 min, all tests pass; in the container with his Codex login). Its token use is recorded.
  - Native Windows: every model call had been failing silently (`claude` is a `.cmd`), so Jarvis answered with canned lines. Fixed (`hive.argv`); Jarvis bench now 20 of 20.
  - `hive name "<startup>"`: Jarvis, the cloud and the AWS machine use the startup's name.
  - Deleting the cloud from the phone: the cloud copy powers its machine off (bill stops, disk keeps the work); `hive cloud --stop` on the computer restarts it, brings everything home, then deletes it. Not yet tried on real AWS.
  - The guard checks builders' own commits (a dependency folder reached main in Gate 38) and no longer fails when the work was already committed.
- **Still to try live:** the phone power-off on real AWS; Gemini and Antigravity presets on real installs (not installed here).
- **Private:** `D:\Suryansh\Programming\hive_private\` (`g36priv`, `g37priv`, `g38priv`, `g45priv`) and `/home/node/g38`, `/home/node/g45` in the container. Never commit `gate7_private.zip`.

## Needs the user

### A person answering live
- Every answer so far came from encoded rules. Have the founder answer builder questions in real time on a small gate; measure consistency with their own rules and answer time (Gate 7's Q2 and Q3, never tested).

### G19 (folded into Gate 20): the company's documents
- The company's policy pages (Notion was unavailable on Oct 27: the connector did not authorize in this session) as the handbook; the confirmed rules answer.
- Publish only anonymized aggregate numbers, as in Gate 7.

## Running on a laptop (Docker)

Workers run shell commands, so run them in a container. Image: `node:22-bookworm` plus `python3 sqlite3 git` and `npm i -g @anthropic-ai/claude-code`, run as user `node`. Mount the repo read-write at `/host/hive` and `~/.claude/.credentials.json` read-only; copy the credentials into the container's `~/.claude/`; work in a fresh clone inside the container (a Windows checkout has CRLF line endings), with `origin` pointed at GitHub. Copy results back out and push from the host.

## Needs design first (write the config and predictions, push them, then run)

### Team notes on a large, coupled project (when one is available)
- Hive now switches team notes on at 10+ builders or 0.5 collisions per landing (untested thresholds). Test them where they could matter: 12 builders on a codebase whose areas share machinery, notes on vs off, ABBA (`gates/gate43/referee/run43.py` as a template).

### Talking on a coupled project (optional)
- Gate 43 found no effect of a message board on the scale project (little to coordinate). If revisited: a project where categories share machinery heavily, 12 workers, same ABBA design (`gates/gate43/referee/run43.py`).

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
