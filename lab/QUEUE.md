# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Where we left off (Oct 30 2026 IST, after Gate 65; Gate 45 day 2 next, with the founder)

- **Gate 60 done** (the user, travelling: "Run the tests as required"): two wings. The cases where two independent builds disagree did not find the owner's decisions: pooled over two rule sets, 20 of 50 decisions right vs 26 for Gate 58's spot checks, from 10 cases vs 29. Two Claude builds disagree on only 19% of the first build's errors. Kill fired; the spotter stays. Gate 58 replicated. Found: on the fresh rule set the skimmer touched every function in the list review, so the skip rule showed him no spot checks (BRAIN §8, 000c).
- **Fast or cheap (product, no gate):** `hive pace fast|cheap`, asked once at the first `hive start` that would use more than one builder; cheap means one builder.
- **Gate 61 done:** the flight log. Six 2-builder teams cleaned up a careful owner's code; none broke any of 700 hidden calls, with or without the owner's confirmed outcomes as tests. Kill fired; no product change.
- **Gate 62 done:** a second build from Opus or Haiku disagrees with the first on at most 25% of its errors (all three extra models 29%); stop fired; two wings is closed for Claude models.
- **Gate 63 done (ship fired):** spot checks on the parts the list review touched, too: 32 vs 24 of 50 decisions, hidden +7.6. The hand-over now spot-checks every part (`spotcheck.order`). For Gate 45 day 2: the founder may now see 40-70 cases after the list; watch where he stops.
- **Gate 64 done** (the user's idea: a strong planner over cheap builders, escalation when stuck): Haiku finished the deep project but at Sonnet's cost and twice the time; the Opus planner did not help; escalation never needed. Kill fired; no change.
- **Gate 65 done:** an Opus spotter found different decisions, not more (32 vs 31 of 50); no change. Bigger models helped in no role tried (Gates 62, 64, 65).
- **Next without the founder:** none is pressing. Ideas: rank spot checks by what is at stake and measure where a tiring skimmer stops; a second vendor's build only after a mechanical test like Gate 62.

## Earlier (Oct 31 2026, after Gate 58)

- **Gate 58 done** (asked for by the user): the combined review (list, then spot checks on every function the list left, each correction applied alone and re-shown) beat the list alone for the skimming owner: 9 vs 4 of 25 decisions, hidden 58.8 vs 43.2%; 9 of 10 corrections confirmed on re-show. Shipped as the hand-over's last step (`hive/spotcheck.py`). For Gate 45 day 2: the founder's real review should use this flow. Re-shows are now one short sentence (12 and 19 words in a real-model check).
- **Fresh install checked (Oct 31):** `pip install git+https://github.com/suryanshranjan/hive` into a clean venv and a new home folder in the lab container; `hive` with no input exits politely, `hive doctor` reports all set. (Windows fresh install not separately checked; `hive doctor` on Windows was fixed Oct 30.)
- **Gate 59 done:** retraining the fast reader with the builder commands failed (58.5% vs Claude 95.4%; kill fired); they stay with Claude. Post hoc, Gate 49's reader holds on an independent exam (80.7%).
- **Antigravity (Oct 31):** the owner has the Antigravity IDE (1.107.0); its agent runs only inside the editor, and its CLI cannot run a headless builder. Hive names any missing agent before a build and points to Gemini. To test Google's models as builders, the owner installs `@google/gemini-cli` and logs in once.

- **Overnight Oct 30 (Gate 45 and his Telegram untouched):** **Gate 50 done**: one builder 12.8 min / $2.94; seven 4.2 min (3.0×) / $5.53; twelve slower than seven. The law's CPU term and coupling term refitted; `hive start` states the speed-cost trade. `tests/test_cloud.sh` has 2 failures (expired-credential cases) that occur without these changes too: check on the Windows machine. **Gate 51 done**: notes at 12 builders not faster (8.0 vs 5.2 min, noisy), CPU not saturated; the size trigger is off. **Gate 52 done** (flight test of `hive start`): 22/22 hidden, 5.3 min, $0.56; the code sheet now replaces the one-by-one assumption review. **Gate 53 done**: the law now sizes the team by the job's independent parts (`law.parts`); the flight again used 1 builder ($0.24), 22/22, and the code sheet caught 2 bugs the hidden tests missed. **Gate 55 done** (the skimming owner): careful review 100% hidden, skimming 65–66% with the list or the conversation; for Gate 45 day 2, expect the founder to behave like the skimmer, and show him less. **Gate 57 done** (asked for by the user): spot checks drew 17 of 30 corrections from the skimmer but the sheet ended no better (7 vs 9 decisions right; hidden 51.2 vs 48.8%): corrections lost turning cases into rules, and some decisions never shown. **Next (wind tunnel, no founder time):** the combined review: list for the headlines, spot checks drawn from every decision the list left unchanged, each corrected case re-run after the fix and shown again. **Gate 56 done**: a short sheet did not help the skimmer (42.0 vs 42.4%); he corrects what he remembers. **Next, with the founder:** Gate 45 day 2 as registered; then spot checks on concrete outcomes ("Ravi's ₹90 refund at day 20 comes to ₹0. Right?") on the decisions where the code made a non-obvious choice, as a way to buy careful attention a few seconds at a time. **Gate 54 done** (three-part flight, real swarm): 27/27 after the hand-over; first launch found a closed input re-asking a builder's question forever (fixed). Hive's own model calls are now counted in the cost it reports (builders and its own questions and checks, separately).

- **Gate 47 done** (asked for by the user): Claude and Codex builders in one swarm coordinate as well as one agent (both mixed teams 1,340/1,340, 100% hidden, 0 breaks; Codex 52% and 73% of landings); a Codex lead works like a Claude lead. Ship fired: `hive start --agent claude,codex`. Cloud power-off from the phone passed live on AWS (after a Windows key fix).
- **Gate 45, day 1 done (Oct 29, 23:00–00:30):** the founder reviewed the code sheet (46 rules) on his phone and marked none (P2 failed). Two restarts on Hive faults, both disclosed: (1) his question "What does this means" was filed as a correction and the page waited (first attempt stopped at page 5 of 40); (2) restarted on 9 pages; after page 3 he asked for rules clear on first reading, so rules 19-46 were reworded (meaning kept, `/home/node/g45/sheet_D_plain.json`) before he saw them. C = `/home/node/g45/sheet_C.json` (equal to the plain sheet). Last session 273 s. **Next (at least 12 h after, so from Oct 30 ~12:30):** write 12 day-2 situations (one per interface case, the experimenter's framing), get his verdicts on Telegram, cold probe and blind judge; build I from goal + C (4 builders); score N0 vs I; RESULTS with the disclosures.
- **Gate 49 done:** Laya trained on 444 owner-style messages read 77.5% (hybrid 94.2% vs Claude 92.5%, Laya answering 56% at 0.55 s); ship fired; `hive/fastread.py` (optional). Trained checkpoint: `/g49/ckpt` in container `hive-laya` (not in the repo, about 1 GB). Next card: retrain with the builder commands.
- **Late Oct 30, "no gaps" (asked for by the user):** Jarvis checks answers by running the code in a throwaway copy ("I tried it: day 8 returns nothing"); warns him unprompted when a builder seems stuck; remembers what he says about his business (to the cloud and back); replies in his script. Real-model Jarvis bench: **29 of 29, mean 8.0** (product questions graded against real code). Conversational review dry-run with the real model: works. `hive doctor` on Windows wrongly said Claude was logged out: fixed. Still to do with him: day 2 of Gate 45; one real build steered from his phone; first-time setup on a fresh machine; retrain the fast reader with builder commands.
- **Tool, from the founder's live review:** the sheet review is a conversation (Jarvis says how each part works covering every rule; he answers in his own words; changes said back; detailed rules one tap away); questions answered by reading the built code; every reply form read for what it is; resumes when cut off; sheets written for first reading; build failures told in plain words.
- **Gate 48 done** (asked for by the user): Laya, the open copy of Jev, read 42.5–45.0% of 120 owner-style messages against Claude's 92.5% (Hindi or mixed 31–41%); fast once set to 2 threads (0.68 s vs 4.2 s); kill fired, Claude stays Jarvis's reader. Next card below: train Laya on the owner's style.
- **Tool, from the phone (asked for by the user):** Jarvis knows the builders' board while a build runs; "who's doing what", "use 2 Claude and 2 Codex" (the law is put to him first when his size differs), "stop w2" (unwanted work dropped), mid-build instructions to the builder whose work they touch (`OWNER.md`; live check: Codex builders built one), rules mid-build reach all builders; a stop it only inferred is confirmed; skip-tests or push-to-main is never a build. 323 checks; real-model Jarvis bench 25 of 26, then the two it flagged fixed (risky 8/10, redirect 9/10).
- **Next:** Gate 45 with the founder (his 46-rule phone review); then train Laya on the owner's style (card below); a gate on whether builders act on mid-build instructions reliably at scale.
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

### (Done, Gate 59: kill fired) Retrain the fast reader with the builder commands
- Not worth repeating as is: 440 items for 13 meanings taught 40.5% on the builder commands. Only with several times more examples per meaning, or with the build's context (whether a build is running, who w2 is) in the reader's input.

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
