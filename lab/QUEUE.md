# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Where we left off (Oct 29 2026, night before Gate 38 day 2)

- **Overnight, separate from Gate 38 (no Gate 38 file, container or Telegram touched):**
  - **Gate 39 done** (wind tunnel, synthetic owner): complete rule sheet 250/250, Hive's interview 76.0%, tour 75.6%, none 38.4%. Leak: 8 of 25 decisions never asked (all unusual input), 4 lost before the sheet. See `gates/gate39/RESULTS.md`.
  - Tool fixes from it (all 203 checks pass): corrections amend the rule instead of replacing it; the terminal restates a rule before its correction; own words keep their detail.
  - **Gate 40 done:** asking about unusual input did not raise coverage (0.64 vs 0.76; +1.2 points); not shipped. Complete sheet 250/250 again. The sheet keeps only 0.69–0.76 of what was asked.
  - **Gate 41 done:** whole rulings beside the sheet cost 6.8 points (kill fired). The merge lost nothing; the loss is coverage (11/25) and answers about one case (7/11 whole). Complete sheet 250/250 a third time.
  - **Gate 42 done, the night's best result:** a rule sheet written from the first build's code, corrected by the synthetic owner, took fresh builders to 99.6% (interview 68.4%, complete sheet 100%). Shipped as Hive's hand-over (`hive/codesheet.py`).
  - **Gate 43** (asked for by the user): talking swarm vs silent swarm on the scale project; see `gates/gate43/`.
  - **Next with the founder (after Gate 38):** the code sheet on his phone for one real feature. Is a 50–80-rule sheet readable for a real owner?

- **Gate 38 is running.** Predictions in `gates/gate38/prompts/PREDICTIONS.md` (`72a5726`).
  - Day 1 is done: Hive's interview (13 questions, one per decision) and the rule sheet; 13 rules confirmed, one corrected, 7.9 minutes.
  - Day 2 is scheduled in the container: `/home/node/g38/day2.py` waits until 06:40 UTC on Oct 29, then puts the 12 referee situations (`cases.json`, cold probe unanimous 12/12) to the founder on Telegram. Log: `day2.log`; answers saved to `verdicts.json`.
  - After day 2: blind judge labels (`judge.py`), confirm free-text readings, then the stability judge (confirmed rules vs day 2, and raw day-1 answers vs day 2: A1, A2), hidden tests and a private reference, the amendment, build arms N and I (I = goal + confirmed rules from `confirmed_rules.json`), score, RESULTS, BRAIN, and a row in `docs/research_to_product.md`.
  - Nothing else may read the founder's Telegram while day 2 runs.
- **Tool (all 203 checks pass on Linux and on GitHub):**
  - Interview from the code's decisions, one question per decision, no repeats, explanations on "what does this mean?", the rule sheet, and the "looks right?" hand-over.
  - The swarm law picks the number of builders; `--docs` reads company documents.
  - Telegram works as an agent: messages are read in the conversation's context (the thread is kept on disk), builds run in the background and report problems, replies are fast and in one voice.
  - Cloud: `hive cloud --new` (real AWS, verified), moving with the Claude login so builders work there; `--stop` brings results, rules and the conversation home, deletes the machine, and resumes listening here.
  - Native Windows (no Docker): every suite passes (UTF-8 for Claude and the builders, paths with spaces, the key made private with icacls).
- **Still to try live:** a full trip from the phone (build in the cloud, status mid-build, a correction mid-question, then `--stop`), after day 2.
- **Private:** `D:\Suryansh\Programming\hive_private\` (`g36priv`, `g37priv`, `g38priv`) and `/home/node/g3x` in the container.

## Needs the user

### A person answering live
- Every answer so far came from encoded rules. Have the founder answer builder questions in real time on a small gate; measure consistency with their own rules and answer time (Gate 7's Q2 and Q3, never tested).

### G19 (folded into Gate 20): the company's documents
- The company's policy pages (Notion was unavailable on Oct 27: the connector did not authorize in this session) as the handbook; the confirmed rules answer.
- Publish only anonymized aggregate numbers, as in Gate 7.

## Running on a laptop (Docker)

Workers run shell commands, so run them in a container. Image: `node:22-bookworm` plus `python3 sqlite3 git` and `npm i -g @anthropic-ai/claude-code`, run as user `node`. Mount the repo read-write at `/host/hive` and `~/.claude/.credentials.json` read-only; copy the credentials into the container's `~/.claude/`; work in a fresh clone inside the container (a Windows checkout has CRLF line endings), with `origin` pointed at GitHub. Copy results back out and push from the host.

## Needs design first (write the config and predictions, push them, then run)

### G43: talking swarm vs silent swarm (about $15)
- Predictions `gates/gate43/prompts/PREDICTIONS.md`. Command: `python3 gates/gate43/referee/run43.py --workers 6`, then `python3 gates/gate43/referee/analyze.py runs/g43`.

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
