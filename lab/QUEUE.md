# Experiment queue and session handoff

Read this after `BRAIN.md`. Pick the top **ready** card. When you finish, update "Where we left off" and push.

## Current implementation handoff (Nov 17 2026)

**Pre-pilot engineering follow-up.** Migration 11 opens uncertain fixed-plan writes for
read-only verification or owner resolution. Undo and temporary preview operations now
use durable approvals, including review withdrawal and cleanup after expiry. The new
`action_boundaries` suite checks the document, filesystem and tool boundaries. The next
rollout step remains the dedicated-account pilot described below.

**November 19 follow-up.** Migration 6 adds durable listener work, task controls, bound replies and
verification evidence. Controlled dispatcher journeys run with `python -B tests/test_dispatcher.py`.
Google and Telegram are unconfigured on this host. The dedicated-account pilot awaits configuration
and publication of its prediction card. Adaptive routing remains opt-in.

The separate Release 2 candidate adds scoped business and memory tools and child builds.
Run `python -B tests/test_build_receipts.py` for exact-commit recovery, missing artifacts,
branch divergence and project-scoped data access.

The Release 3 candidate adds the optional host-local control gateway, mobile noVNC
view, MCP OAuth grants and containerized stdio connectors. Setup and reverse proxy
configuration are in `docs/control_gateway.md`.

The Release 4 candidate adds zoned calendar schedules, deduplicated signed events and checked cloud handoff in migrations 9–10. See `docs/schedules_and_handoff.md`. Run the schedule and handoff suites plus the Linux shell cloud regression. The handoff tests cover a return from a separate installation, retained unresolved work, changed account bindings and missing artifacts. The phone sign-in fixture uses mobile viewport and touch emulation. A physical phone, live providers and an SSH host remain rollout checks.

- **Publication:** owner requested committing and pushing the runtime changes. README now
  leads with the phone workflow and includes adaptive/MCP/browser/routine setup, saved-task
  controls, local verification results and remaining live-account limits. Local documentation
  links and anchors checked; research predictions, scorecard and measured constants unchanged.

- **Adaptive follow-up implemented:** `agent:` or `HIVE_ROUTER=adaptive` selects the durable
  observe/act/replan loop. MCP Streamable HTTP tools, Docker browser control and interval
  routines are available. Business-goal plans save steps, answers and their own build state;
  confirmed action receipts reconcile without re-executing writes. Setup/limits:
  `docs/adaptive_tasks.md`. Unknown writes/build steps still require inspection.
- **New evidence:** full Docker regression 48/48 suites; final selection 9/9; expanded adaptive suite 22/22 on
  Windows; MCP protocol fixture 5/5; real Chromium 3/3; host browser IPC/mount check 1/1.
  Initial Chromium sandbox startup failure was fixed by allowing inner-sandbox `chroot`
  while retaining all outer capability drops. Read-only readiness probe: Google and
  Telegram not configured. No model experiment or live-account writes.
- **Next:** configure accounts on the intended host and qualify live-model replanning,
  provider reads/writes/readback, authenticated browser flows and external MCP services.
  Also qualify interrupted build effects and moved project paths. Opt-in runtime remains
  bounded by available tools; recurrence is interval-based and needs the listener running.

- **Task/context follow-up:** SQLite migration 4 checkpoints static router chains. `tasks`,
  `task <id>` and `resume task <id>` inspect/resume progress; completed steps are skipped,
  duplicate deliveries reuse their task, and interrupted writes stay blocked. Owner/chat/project
  scope and mail/calendar configuration hashes bind recovery. Only interrupted `mail_find`
  and `calendar_check` reads are retryable on explicit resume. Conversation storage keeps 32
  complete entries; rendered context has a 24k-character budget with visible omissions.
- **Follow-up verification:** 19 new task/context tests pass on Windows; Docker selections
  passed 9/9 and 7/7 suites (the final selection includes all 19 new tests). No live models or
  accounts. See `docs/reliability.md`. Adaptive planning, business-goal build recovery and
  receipt reconciliation are covered by the subsequent implementation above; live
  qualification and task mapping across changed project paths remain open.
- Reliability changes and the Gate 120 routing results are included in this handoff. P0/P1 are not considered production-closed.
- Implemented: durable, exact action approvals; request-origin checks; authoritative SQLite memory and ordered extraction jobs; scoped/temporal retrieval and deletion tombstones; atomic Pulse checkpoints, delivery claims and non-consuming digests; Telegram batch persistence; isolated execution requirement and real Windows ACLs.
- Verify with `python tests/run_reliability.py --fixture-execution` (controlled fixtures only). Windows ACL tests need a normal user token; removing inherited rights intentionally prevents the restricted sandbox token from writing those test paths.
- Docker runner `hive-builder:3` includes required encryption dependencies; real worker-boundary and timeout-cleanup checks passed locally. Cloud return now snapshots SQLite and refuses local divergence. Voice transcripts retain owner provenance and temporary audio is removed. Commands and limits: `docs/reliability.md`.
- Final local verification: **45/45 Docker fixture suites passed**, including 40 failure-journey unittests. The Windows reliability/Telegram/voice selection passed 3/3; installed-command/cloud-return Docker selection passed 3/3. Hosted CI has not run for this working tree.
- Still to validate: real Gmail/Calendar and Telegram delivery, restore/move on real machines, live saved-chain recovery, Hindi-English audio quality. Keep `HIVE_ROUTER=plan` opt-in until chain execution qualifies.

## Where we left off (Nov 15 2026, late: capability audit, then P0 security)

- **Done, pushed:** the builders' sandbox (`hive/sandbox.py`; real checks with stand-in builders, Claude Code and Codex). Earlier: the capability audit and the approved Telegram-first plan (`docs/jarvis_plan.md`; out of scope this phase: web, phone apps, desktop, calls). P0 first round (BRAIN §12): encrypted secrets (`hive secrets`), Render pairing word, shell quoting, guard refuses when main's tests are unreadable, suite and builder time limits, secret-free builder environments, outside text marked as data, `hive audit`. All 36 test files pass on Windows.
- **Done since:** Gate 120: messages read as a plan of steps (now the default; chains 14/14, single messages as accurate). **Next:** routing on the small model (each reading call costs about $0.09 on the default model). P2 Pulse, P3 voice replies, P4 tool registry and policy, P5 Google over REST (built and tested with stand-ins; BRAIN §12). **Next to fly with him:** Pulse on his real mail and calendar for a day (what interrupted, what should have); "connect google" on his real account; a voice note round trip on his phone. **Next without him:** a routing gate before replacing the reader with native tool calls. Earlier: a real two-builder Claude build in the sandbox (11/11, $0.42); P0 closed (claims, Render as its own user, the cloud move names his data sources); memory 2.0 built and wired in; Gate 118 scored (`gates/gate118/RESULTS.md`: recall 30/30 vs 2/30; changes replace old facts; memory calls on the small model).
- **Next, in order:**
  1. **Leftovers done** (BRAIN §12, "the leftovers fixed"). P1 memory is complete: recall by words and meaning, changes of mind, people, deadlines, forgetting, a weekly tidy (Gates 118-119).
  2. **P2 Pulse:** `hive pulse` (a second process, never reading Telegram): watchers for mail, calendar (fix TZID first), payments, builds, deadlines (the store's `valid_until`); triage on the small model; quiet hours and his rules; no duplicates.
  3. P3 voice replies (Piper), P4 tool registry, P5 Google over REST (`docs/jarvis_plan.md`).
- **Still waiting on him:** Gate 117 (real Render, now with the pairing word), Gate 114, his real mail/calendar/payments, the founder session.

## Before that (Nov 15 2026 evening; the owner: "we will pick up the rest later")

- **Done today, pushed:** Gates 115, 115b, 116 scored (BRAIN §5). The planner asks up to 3 specific questions (default); a messy picture still beats words; a failed fast-reply provider rests 10 min; the Render image builds, and a bad bot token stops the deploy plainly.
- **Waiting on him, in order:**
  1. **Gate 117, real Render** (`gates/gate117/`): he puts `RENDER_API_KEY`, a new bot's `TELEGRAM_BOT_TOKEN` and `ANTHROPIC_API_KEY` in `~/.hive/render_test.env` (never in the chat), then `python gates/gate117/render117.py up`; he says "hi" to the new bot; `logs`; a redeploy; `down`.
  2. **Gate 114** (`gates/gate114/flight114.py`): `aws-renew` (the laptop's AWS sign-in is expired), `limit`, `cycle`, `fast` (after `hive llm api`).
  3. His real mail, calendar, payments ("connect my email" on the phone).
  4. The founder session (`docs/founder_session.md`).
- **Next without him:**
  - a follow-up question when his answer only half-says the fact (Gate 115b's two misses);
  - asking fewer when nothing is hidden;
  - his own phone photos for Gate 116.
- **Small, his call:** commit or delete the untracked Gate 109-113 run logs.

## Before that (Nov 15 2026, after Gates 115-116 and Render)

- **Gate 115 done** (`gates/gate115/RESULTS.md`): the planner asks up to 3 specific questions about what only he knows (8/8 vs 4/8, simulated founder; inflated by a founder who over-shares). Now the default.
- **Gate 116 done** (`gates/gate116/RESULTS.md`): photo of a screen 17/19, busy screenshot 18/19, clean 19/19, words 11/19.
- **Render / only a phone:** built and unit-tested (`tests/test_render.py`), never deployed. To fly it, he: makes a bot with BotFather; opens the Deploy to Render link from the README; fills `TELEGRAM_BOT_TOKEN` and `ANTHROPIC_API_KEY`; says "hi" to the new bot; deletes the service afterwards (~$28 a month).
- **Next without him:** Gate 115b: a stricter simulated founder who answers only what is asked, and asking fewer when nothing is hidden (it asked 3 on the control).
- **Next with him:** Gate 114 (below), a real Render deploy, his own phone photos for Gate 116, the founder session.

## Before that (Nov 15 2026, the owner: "let's fix it all"; Gate 114 registered)

- **Built and unit-tested, not flown** (`gates/gate114/PREDICTIONS.md`):
  - fast replies with any provider's key (`hive llm api`), streamed (`tests/test_fast.py`);
  - a limited AWS login (`hive cloud --limit`), a warning on root, and the AWS expiry check on Hive's own login (`tests/test_aws_limit.py`).
- **Next, in order (`python gates/gate114/flight114.py <part>`):**
  1. `aws-renew`: the laptop's AWS sign-in has expired by itself; he renews it from the phone (part A).
  2. `limit`, then `cycle`: the limited login checked with dry runs, then a t3.small made and deleted as `hive-builder` (parts B, C).
  3. `fast`: once he runs `hive llm api` with a key (part D).
  4. Part E: he says "connect my email / calendar / Stripe" on the phone.

## Before that (Nov 15 2026 morning, after the night's work: Gates 111-113)

The owner said "fix everything" toward a Jarvis for the whole company, chose the order (always on first), then "complete everything, I'm going to sleep".
- **Gate 111, always on is his choice** (`gates/gate111/RESULTS.md`). The phone and setup offer this computer (free), small (~$23 a month) or bigger (~$72), priced from AWS's list. Attempt 2 held on all predictions on real AWS. Fixed from attempt 1: ssh had no timeout; an old hand-over was replayed in the cloud.
- **Gate 112, his office: mail, calendar, payments** (`gates/gate112/RESULTS.md`).
  - **What it covers:** any IMAP mailbox, Gmail included, read without marking read, replies only on his yes; Google Calendar by its private iCal address; Stripe and Razorpay, read-only.
  - **How it was flown:** on GreenMail and stripe-mock with the real model. Run 3 held on all 7 predictions.
  - **Secrets** are deleted from the chat and from Hive's record of the conversation.
  - **His real accounts are not connected yet.** He says "connect my email", "connect my calendar", "connect Stripe" or "connect Razorpay" on the phone.
- **Gate 113, Gate 108 on a second company** (FixKaro, appliance repair; key in `hive_private/fixkaro/`). Everything held:
  - 9 of 10 figures;
  - the hidden rule found;
  - the planner's price rule replicated;
  - screens on re-run, after my launch lacked the browser path.
  The one miss, a deduction taken twice, is fixed (3/3 re-asked).
- **One-line installers:** `install.sh` (Linux, macOS) and `install.ps1` (Windows). Tested on a bare Ubuntu container and on Windows.
- **Faster replies, measured:** a reply is mostly the model's own time (7-8 s for reading a message; Haiku saves about 1 s). The real speed-up needs an Anthropic API key and streaming; there is none on this laptop. Meanwhile, mail, calendar and payments say at once what they are doing.
- **Phone-only setup:** the computer part is now one line plus `claude` and `hive setup`. A setup with no computer at all needs Hive hosted for the founder: the owner's call.
- **AWS:** nothing of Hive's is left (checked). His `barternow-staging` runs, untouched. The lab's Docker test containers are removed.
- **Next (his word needed):**
  1. connect his real mail, calendar and payments, and fly Gate 112's questions on them;
  2. an Anthropic API key, for faster replies;
  3. Render as a second always-on choice (he asked; to discuss);
  4. the founder session.

## Before that (Nov 15 2026, after Gate 110)

- **Gate 110 done** (`gates/gate110/RESULTS.md`): Vercel from the phone on the owner's personal Vercel. Attempt 3 held on every prediction after the first-deployment fix. Everything the test made is deleted; his `portfolio` is untouched. Vercel's tool is installed on the laptop (Hive installed it), signed in to his personal account.
- Still unflown: a login renewed from the phone (all were valid); a framework build on a host.

## Before that (Nov 15 2026, after Gate 109)

- **Gate 109 done** (`gates/gate109/RESULTS.md`): the cloud paths on real AWS, t3.small. The move, the restart in the cloud with his answers, the work home and the delete all held. The test page failed (its stop command killed its own shell), was fixed, and held in flight 109b. Nothing of Hive's is left in AWS (checked); only the owner's own `barternow-staging` runs there, untouched.
- Fixed from it: questions to the phone one at a time; a test-only machine is a t3.small.

## Before that (Nov 14 2026, after Gate 108 run 4)

- **Gate 108 done, replicated** (`gates/gate108/RESULTS.md`): runs 3 and 4 clean in a row; run 4 found all 4 planted problems after the planner's price rule. Dabba Days lives in the lab container (`~/dabba-days`, `~/dabba-data`; key in `~/dabba-private` and `hive_private/dabba/`).
  - Its data is also in Postgres (`dabba-pg`) and MySQL (`dabba-my`) on the Docker network `hive-db`, with read-only login `reader`/`readpw`. Hive read both: 5 of 5 right each.
- **Built and unit-tested, not flown:**
  - "I'm sleepy" to the cloud with a restart there (`hive/assistant.py` `away`);
  - expired logins renewed from the phone (`hive/logins.py`);
  - test deploys on his AWS machine (`hive/trydeploy.py`).
- **AWS** is signed in on the laptop (account …1696, root login; a limited user would be safer).
- **Gate 109 attempt 1 (Nov 15):** interrupted, because the laptop ran low on memory while the machine set itself up. The machine was deleted and checked in AWS; nothing is billing. One fix: deleting a machine never moved to no longer asks for a safety word (`gates/gate109/RESULTS.md`).
- **Next:**
  1. (Done: Gate 109.) Still unflown: an expired login renewed from the phone, against real AWS and GitHub.
  2. The founder session (`docs/founder_session.md`).
  3. Gate 108's design on a second mock company in another trade.

## Earlier (Nov 14 2026, before Gate 108)

- **Built on the owner's request: run the company through Hive (unit-tested, not flown).**
  - "set me up" onboarding with three paths: a business, a developer with a product, or something new (`hive/onboard.py`).
  - Read-only access to his data, and answers from it (`hive/access.py`, `hive access`).
  - Screenshots on phone, tablet or desktop of the pages he names.
  - The interview skips what he has already said.
- **Next:** fly it.
  - A fresh founder runs "set me up" on the mock Sunny Shop, with a SQLite copy of its orders, then asks figures questions. Score the answers against the data.
  - Then a developer on his own product.
  - Then the founder session on his real product.

## Earlier (Nov 3 2026, after Gate 107)

- **Gate 107 done (ready for a second founder):** the full founder journey, 14 steps on the phone, passed in runs 3 and 4 after two fixes (builds from the phone go on top of his latest unmerged build). Not yet flown: the brief greeting at his clock (fixed after run 4). Next: a second founder on a practice project, then on his real product.
- **Product rounded out (not yet flown):** the missing-question before a plan, numbers (`hive numbers`), the morning brief, hosts (`hive deploy setup <host>`: preview links, live only after a merge), `hive up`. Next: test it all, then the founder session on his real product.
- **Gate 106 done (ships):** business in, plan out. With only a business goal, Hive planned and built 8 of 9 planted problems on a mock creator site (4 owner messages, 0 technical words, $0.88-1.45 a goal). MiroFish read (AGPL, ideas re-implemented): the customer panel added nothing, off. Private files: `private/g106` on the laptop lab. Next on this thread: what the product doesn't show (BRAIN open question 0000, the first one), then a real product.
- **Gate 105 done (all held):** his reference picture vs his words for a look, one fix round each: 18/18 vs 13/18 measured checks, blind judge 3 of 3 for the picture, same cost ($0.26 vs $0.25). Jarvis now suggests a screenshot when he describes a look in words. Targets and checks are in `private/g105` on the laptop lab (Docker `hive-g8`). Next on this thread: a picture from the wild (BRAIN open question 0000, the first one).
- **Built on the owner's request (Tony scenario):** "ship it" from the phone (`hive/ship.py`, a pull request after he confirms, never his main); a customer's complaint traced to his rules or to a fault (`assistant.complaint`). Tests: `tests/test_ship.py`, `tests/test_complaint.py` (in CI).
- **Lab:** Playwright and Chromium are now in the container (`PLAYWRIGHT_BROWSERS_PATH=/home/node/.cache/ms-playwright` under a clean home). The real home's Claude login now links to the live host login (`/host/creds.json`; the old copy is kept as `.credentials.json.bak-nov2`). A mock project for the live phone loop: `/home/node/sunnyshop` (origin `/home/node/sunnyshop-origin.git`).
- **Live with the founder (Nov 3 evening):** he asked from his phone to redo the Sunny Shop practice page in barternow.in's style. Fixed what it exposed: look jobs (one builder, no quiz, research note, screenshots with what changed), one-line restatements, no false alarm on a deliberate stop, one listener only (two were answering him), and `telegram._alive`, which on Windows terminated the process it checked. The listener runs in `hive-g8` on `/home/node/sunnyshop` (`python3 -m hive listen`, HOME=/home/node). The interaction map and what's next: `docs/jarvis.md` (a daily brief first).
- **Next with the founder:** the live phone loop (show me, a picture, ship it, a complaint) on the mock Sunny Shop; then the founder session (`docs/founder_session.md`).

- **Gate 103b done, ships** (flown Nov 3 on the user's laptop, Docker lab): live 26, 27, 27 of 27 with the owner's-examples check (it caught a split-payment refund in live 2); X1, X2 held, X3 failed on minutes (+11.3, confounded: slower machine, and live 1 stalled about an hour while the laptop ran out of memory). Drift F3 not flown: `private/g92` and `runs/g101_day1` exist only on the cloud lab. The check stays on.
- **Gate 104 done, ships** (Gap 2): confirming his rules once on the sheet (no own-words read-backs) took the median owner prompts from 30 to 23, every build 27/27; now the default. Next on owner time: the after-build review that runs when builders ask fewer than 3 questions (those flights cost 36-42 prompts).
- **Also Nov 3:** CI was red since Nov 2 (test_telegram reached the real Claude before its stand-in was set); fixed. test_law wrote the owner's real `~/.hive/pace` on Windows; fixed, and the stray file removed.
- **Next:** the founder session (`docs/founder_session.md`); drift F3 of Gate 103b only if the cloud lab's `private/g92` is reachable.

- **Gate 66 done (the user, travelling: "test something that makes Hive the best tool"):** one Claude Code agent that asks the owner beat Hive's hand-over by 21-30 hidden points (CQ 93.0, CC 84.6, HV 63.4, N0 34.8%) at 1/13 of his reading. Wind tunnel, synthetic owner who answers from his policy.
- **Gate 67 done:** the hand-over's memory does not compound (neither rule fired).
- **Gate 68 done (rule fired, shipped):** Hive's swarm asking first = one agent asking (98.4%); the hand-over after added +1.6. Builders now ask first; the hand-over is skipped after a build whose builders asked 3+ questions.
- **Gate 69 done:** memory of answers and house rules did not compound with asking builders.
- **Gate 70 done (ship fired, shipped):** overnight questions answered in the morning 94.2% vs morning hand-over 75.0%.
- **Gate 71 done (claim did not fire):** with the owner at 60 s an answer, one agent and the 7-builder swarm both took 48 min; the swarm 85.4% vs 94.1% (questions lost to the 2-minute cutoff; `hive ask` fixed). g71b was rerun after the 04:10 container restart.
- **Gate 72 done (claim did not fire, narrowly):** mixed job, owner at 60 s: the swarm reached 95% 2.4-7× sooner and finished 0.77× the time at 2.9× the cost; engine as right, business 93.8 vs 97.2%. Shipped from its first run: one answer serves a repeated question.
- **Gate 73 done (claim did not fire):** the repeated-question rule kept the swarm's questions at one agent's level but its business rules stayed less right (89.8 vs 97.0%); Hive asking first flooded the owner (65 questions, 64 min).
- **Gate 74 done (shipped the split):** 6 engine builders plus 1 business builder: business rules 97.8 vs one agent's 95.2%, engineering 95% in 4.9 min; to all visible tests no sooner (1.05×; by wall 0.81×). Hive now gives the owner's decisions to one builder when he is there and there are 3+ builders.
- **Gate 75 done (claim fired):** on an engineering-heavy job the split swarm reached one agent's accuracy (90.0 vs 86.5%) in 0.45× the time (12.1 vs 27.1 min), at 1.95× the cost.
- **Gate 76 done:** the shipped flow flies: live 27/27 (split engaged, review skipped), overnight 22/27 after `hive morning`.
- **Gate 77 done (claim did not fire):** splitting the night builders scored 25.7 vs 25.0 of 27 after the morning (3 flights each), with 1.28× the morning questions. Not shipped (`HIVE_SPLIT_OVERNIGHT`, off). Gate 76's overnight 22 was a low draw.
- **Gate 78 done (M1 failed, not shipped):** a graphify map of sqlglot in every builder's clone; no builder opened it (the goal named every file; 2-4 min jobs). `hive/codemap.py` stays off. The lab now has its own map: `python3 lab/graphify_lab.py`, then `graphify explain "Gate 74" --graph runs/lab_map/graphify-out/graph.json`.
- **Gate 79 done (claim did not fire):** on sqlglot bug reports with no file names, the map guided by graphify's rule and hook was run 6 times by 12 builders; cost 1.07x, time 0.88x with its build; not shipped. Areas per report stopped duplicated work.
- **Gate 80 done (shipped):** with no areas configured, Hive now names the goal's parts as areas: functions rebuilt twice 5.7 -> 0 of 12, cost 0.90x.
- **Gate 81 done (two faults found, fixed):** one builder claimed all derived areas; a refused builder landed anyway. Now: even-share claims, `hive land` needs a lock (exit 9), derived areas re-derived per goal.
- **Gate 82 done:** claim fixes held in flight (live 27/27); landed areas looked free and were reclaimed; fixed (`hive areas` shows landed; `hive claim --again`).
- **Gate 83 done:** derived-area claims fly cleanly (Gates 80-83 close that loop). Live scored 14/27: the business builder changed `refund()`'s result shape after an owner answer, and the review was skipped after 3 questions.
- **Gate 84 done (on by default):** when the review is skipped, Hive checks the goal's stated interfaces; it repaired Gate 83's build (14 -> 26/27) and raised no false alarm in two flights.
- **New phase: closing the founder's gaps** (`docs/gap_plan.md`): reliability (pass^k), owner load under 10 minutes, Hive's own spend, real codebases (Ambig-SWE), owner drift, the real founder, MAST failure labels.
- **Gate 85 done (baseline):** pass^1 0.80, pass^5 no; median 55 owner prompts; Hive's own spend 4.8-8.6x builders' (interview interpretation 45%, reply reading 19%, spot checks 22%).
- **Gate 86 done (claim did not fire):** real Django issues: one builder 8/10 full, 7/10 summary; hive start 8/10 at 15x the cost; the business interview invents a shop on technical goals.
- **Gate 87 done:** Haiku for Hive's own reading: spend 0.11x, pass^1 same, median hidden 25; found the placeholder fault (split x derived areas).
- **Gate 88 done (claim fired):** at most 6 spot checks: prompts 34 vs 55, pass^1 1.00; ships after Gates 89-90 (3 of 5 reviews were skipped, so partly luck).
- **Gate 90 done (claim fired):** the business builder fills placeholders; none left. One flight failed on a review correction that changed `refund()`'s result shape: the interface check must run before every delivery.
- **Gate 89 done (claim did not fire):** no interview on technical goals (10/10), kept on business ones; the review is the load.
- **Gate 91 done (claim did not fire):** Haiku for Hive's own reading: spend 0.07x but median hidden 25 again; not shipped.
- **Merged to main (`767d66d`):** at most 6 spot checks; the interface check before every delivery; technical goals skip the business review.
- **Gate 93 done (new baseline):** 33 owner prompts (55 before), pass^1 0.80, pass^5 no (an unsafe new default: `delivered=False`).
- **Gate 94 done (claim fired):** technical goals skip interview and review: 8/10 Django issues, 0 prompts, $3.64 (was $19.72).
- **Gate 92 done:** memory is safe under announced drift (29/29 either way); saves no prompts.
- **Gate 95 done (claim fired):** the ordinary case first: 5 of 5 flights right, 31 prompts. One flight's difference: repeat.
- **Gate 96 done:** pass^5 held again: 10 of 10 flights over Gates 95-96.
- **Gate 97 done (claim fired):** lean reader: Hive's own spend 0.16x, about equal to builders'; ~$0.97 a feature; interface check now follows helpers.
- **Gate 98 done:** lean reader + helper check: 5/5 right, ~$0.94 and 4-10 min a feature, 28 prompts.
- **Gate 99 done:** overnight path: $1.09 a feature, 14 morning prompts, pass^1 0.60 (decisions no night builder asked about). Guard snapshot leak fixed.
- **Gate 100 done:** harder Django issues: 9/9/9 of 10, 0 prompts; public summaries no longer hurt modern builders. Gap 4 needs the founder.
- **Gate 101 done:** silent drift: memory kept 27-29 vs cleared 20, 29, 17 of 29; the contradiction check notices the change.
- **Gate 102 done (shipped):** the interview before an overnight build: 5 of 5 overnight flights 27/27, 30 prompts, $1.53.
- **Gate 103a done:** the owner's-examples check, replayed on 32 builds, flags both Gate 101 verification failures and 1 of 23 good builds, $0.11.
- **Gate 103b, 2 of 6 flights done** (dev103 merged as `62ddaed`, **under test**: the owner's-examples check runs before every delivery):
  - Drift F1 and F2 scored 29 and 29 of 29 (Gate 101 without the check: 20, 29, 17). In F1 the check caught the old points rate, and one builder fixed it.
  - **Next session, first thing:** fly the rest, one at a time, with `~/.hive` absent:
    - `python3 gates/gate103/referee/flight103_drift.py day2 F 3`;
    - `python3 gates/gate103/referee/flight103_live.py live 1`, then `live 2` and `live 3`.
  - Then run `python3 gates/gate103/referee/analyze103b.py` and write `gates/gate103/RESULTS.md`'s 103b section.
  - If X1 and X2 hold, it ships. Otherwise `git revert -m 1 62ddaed`.
  - Turning it off without a revert: `HIVE_EXAMPLE_CHECK=0`.
- **Next, in order:**
  1. Finish Gate 103b.
  2. Owner time (Gap 2). Gates 95–98 and 102 average about 11 interview questions plus 9 per-answer rule confirmations per feature. The synthetic owner adds detail at most confirmations, so test whether one batched confirmation at the end loses anything.
  3. The founder session (`docs/founder_session.md`).
- **Next ideas:** the default model only where answers become rules (Gap 3); Gap 4 again on harder issues; the founder session (`docs/founder_session.md`).
- **Next:** skip the interview when a goal has no business decisions (Gate 86); Gap 4 again on issues whose summaries lose what a builder cannot infer (Ambig-SWE's missing-information annotations); a check for state that outlives a call (Gate 85) on a real codebase (where 'business parts' are a judgement); low priority, a short interview before an overnight build (at most ~2 of 27 to gain); the split on a real codebase (where 'business parts' are a judgement); with the founder, Gate 45 day 2 with builders asking him live (his pace and whether his answers hold).
- **Earlier plan, superseded by Gate 73:** Gate 72 again with the repeated-question fix (does the swarm then match one agent's business correctness and keep its speed?). **With the founder:** Gate 45 day 2, builders asking him live; measure his answer time and whether his answers hold.
- **For Gate 45 day 2 with the founder:** test builders asking him live (his answers drift; does asking still win?).

## Earlier (Oct 30 2026 IST, after Gate 65)

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
