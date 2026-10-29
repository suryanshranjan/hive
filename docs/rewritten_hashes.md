# Rewritten commit hashes

On 2026-10-29 every commit message was rewritten to drop a co-author trailer. File contents did not change, but every hash did. Gate RESULTS.md and PREDICTIONS.md files cite the old hashes (for example as proof that predictions were pushed before a run). Look an old hash up here to find the same commit now.

| old | new | subject |
|---|---|---|
| `6e9e0bf` | `50d614b` | Queue: hand-off line for team notes |
| `e33d41b` | `d3859a8` | Team notes, switched on by the law: hive land --note and hive notes; off below 10 builders unless the swarm's collisions reach 0.5 per landing; every rebase conflict shows recent notes |
| `552a8c8` | `45167ce` | Gate 44 scored: the code sheet takes builders to 100% silent or talking; talking adds 0.0 on top and +4.0 without; Hive stays silent |
| `69fd49a` | `135e899` | Gate 44 preregistered: 2x2 of Hive's corrected code sheet (none / sheet) and builders (silent / talking) |
| `de27e43` | `42d930f` | Gate 43 scored: a talking swarm finished the same as a silent one (3.6 vs 3.5 min, cost 1.01x, same correctness); Hive stays silent |
| `fed7692` | `876ea9c` | Gate 42 scored: a rule sheet written from the built code, corrected by the owner, 99.6% hidden vs the interview's 68.4% (synthetic owner); shipped as Hive's hand-over |
| `0d9d45e` | `1b8d3e7` | Gate 43 preregistered: a talking swarm (shared message board) against a silent swarm, scale project, 6 workers, ABBA order |
| `a21ce06` | `61d41a8` | Gate 42 preregistered: a rule sheet written from the built code, corrected by the owner (C), vs the interview (H) and the complete sheet (R) |
| `a92d395` | `ac9eb62` | Gate 41 scored: whole rulings beside the sheet cost 6.8 points (kill fired); the merge lost nothing; the leak is coverage and answers about one case; complete sheet 250/250 a third time |
| `d27a1cc` | `1a61f41` | Gate 41 preregistered: one interview, two hand-overs (sheet alone vs sheet plus every ruling kept whole); R replicates the ceiling |
| `c63c0df` | `509168d` | Gate 40 scored: asking about unusual input did not raise coverage (0.64 vs 0.76, +1.2 points), not shipped; complete sheet 250/250 again; the sheet keeps 0.69-0.76 of what was asked |
| `8a8d49a` | `6c5d8e6` | Gate 40 preregistered: unusual input as owner decisions (interview inputs=True, up to 30 questions) vs the interview as now; R and T replicate Gate 39 |
| `7843de1` | `10c283e` | Gate 39 scored: a complete rule sheet 250/250; Hive's interview 76.0% with a perfect owner; leak is coverage of unusual input and corrections that replaced rules |
| `8e73fb2` | `bd8816f` | Gate 39 preregistered: a wind tunnel for Hive's interview (synthetic owner with exact rules; N0, H, R, T) |
| `b9075c0` | `4a27b9b` | Windows: the cloud key is made private with icacls (Windows' ssh refuses an open key); every suite now passes natively on Windows; handoff notes for Gate 38 day 2 |
| `192eae0` | `c92a460` | Windows: UTF-8 to and from Claude and the builders, paths with spaces, and tests that can never run outside their own folder |
| `f1b2d6a` | `5093983` | Seamless between this computer and the cloud: the conversation is kept, moves with Hive and comes home; --stop brings rules back and resumes listening here |
| `f845fa1` | `a6a6ff3` | Hive on Telegram works like a proper agent: each message read in the conversation's context; builds run in the background and report their problems |
| `91c699d` | `b08df0e` | In a Python environment (as on a cloud machine) builders use that environment's Python, and the cloud copy installs pytest with Hive |
| `c0e7bdb` | `dfb06a7` | Closing the cloud machine brings the work back first: `hive cloud --stop` pulls every result branch, then deletes |
| `101c6ea` | `a614299` | In the cloud, builders can work too: the move brings the Claude login (recommended), and Hive checks Claude answers there |
| `6e72442` | `20122f1` | Hive's replies no longer name the project's folder (it said "your shop project") |
| `b9feba6` | `2d56d52` | Hive answers fast: "typing..." at once, no model for "hi" and "status", a time limit on the voice, brief reasoning for the backup, and Claude skipped while down |
| `93e2103` | `72b7217` | Hive's voice talks like a person: "your project", no folder or branch names, no labels; it says "deleting" only when it can |
| `17f97fa` | `b57a280` | Hive on Telegram handles the owner like Jarvis: messages read together, repeats answered once with an apology, replies in one calm voice from real facts |
| `b5e0995` | `9996e4e` | The listener never goes silent: an old tap, a failing message or a Telegram error is survived; the hand-over to the cloud starts clean |
| `e7bb140` | `dc5cbca` | The research steers the product: the swarm law sizes the team, --docs reads company documents, and an audit maps every finding to code; Windows fixes |
| `988de39` | `f5e292a` | One-step cloud verified on real AWS: ready in 2.5 min, tests pass there, branch pulled back, SSH open to one IP only, nothing left after --stop |
| `626022a` | `e70f82f` | One-step cloud: `hive cloud --new` makes a machine on the owner's AWS account and moves Hive there; `--stop` deletes it; "move to the cloud" works from the phone |
| `be89925` | `2b6f53c` | Every answer, tapped or typed, can settle later questions: Hive drops what it already knows |
| `cd59197` | `65308ee` | Hive reasons about each reply: "what does this mean?" gets an explanation, and a choice said in words counts as that choice |
| `72a5726` | `8a90308` | The rule sheet, the hand-over, hive setup, voice as an install extra, and CI; Gate 38 registered |
| `38ef782` | `4193ba6` | Gate 37: coverage solved (6/6) and answers reached the code, but the owner's answers to two framings agreed 1/8 and 3/6; no gain (kill fired) |
| `f5fccc1` | `ec7a51d` | Interview without repeats: one question per decision, and answers that settle later questions skip them |
| `d7d6c85` | `f44ae02` | Gate 37 amendment before the build: 4 surprising and 4 ordinary cases scored; C2 held (6/6), K1 failed (3/6), S4 failed |
| `0a4b3a7` | `5451a2e` | README: ask-first interview, voice notes, picking up again; Gates 35-37 in the evidence table |
| `64129fc` | `c369b1a` | Queue and brain: Gate 37 pilot done (interface-based interview 7/9 coverage vs 3/9); Gate 37 running on the founder's phone |
| `a033cd9` | `721129d` | Gate 37 registered: interview from the code's decisions vs no owner on content approval, plus a retest of the owner's consistency across framings |
| `8c3414f` | `277251d` | Interview asks about every decision the code takes; Gate 37 pilot: from the interface 7/9 coverage, from the description 3/9 |
| `f91d510` | `0b83b7f` | Gate 37 pilot registered: decisions-first interview coverage on Gate 36's hidden set (no founder time) |
| `d3aff7b` | `459c8a8` | Gate 36: interview first did not carry the owner's surprising rules (kill fired); coverage 4/9, and his answers depended on the framing |
| `9711573` | `db6ffd0` | Interview answers are checked against earlier rulings; build stops reach the owner |
| `6607ca4` | `43236ef` | Builds pick up again after Claude's login expires, and say so plainly |
| `d946e69` | `7d02dd0` | Gate 36 amendment before the build: 7 surprising, 2 ordinary scored; the interview was damaged by a tool bug (S4 failed); arm I gets 9 rules by the fixed reading logic |
| `89472c9` | `deb3c0a` | Hive picks up again: after a usage limit, a stopped process, or a tap on an old message |
| `e1778da` | `2938509` | Telegram: a dropped connection or a second reader is retried, never fatal |
| `cd18e3a` | `6de5bf6` | Telegram: voice notes, a richer chat look, and long options that fit |
| `7166c26` | `1160e1b` | Gate 36 registered: interview first (Hive writes its own questions) vs no owner, judged on an independent hidden set |
| `1ad4876` | `dcedb37` | Interview first: before building, Hive asks the owner the situations where his rules matter; MIT license |
| `3e4fd18` | `52b7a2c` | Gate 35: the founder marked none of 27 decisions (kill fired); his rules come out in situations, not audits |
| `bd3ff8f` | `a14765e` | Review: say plainly that the listed decisions were made by the builders on their own |
| `0ccd9c2` | `574ce3b` | README rewritten product-first; clearer `hive --help`; plan adds M9 (always on, anywhere) and M10 (the review) |
| `80c7f38` | `8c5f81f` | Gate 35 amendment before the build: 8 surprising, 4 ordinary (blind judge); founder confirmed 4/4 readings; 7 surprising scored |
| `928f545` | `795962c` | After the fix round, each change comes back as built for the owner's final yes |
| `a05b4d9` | `188205a` | Gate 35 registered: the real founder as owner on plans and payments, with the fixed answering step |
| `209c42a` | `fe88d12` | Gate 34: the stand-in gave 1 surprising verdict (not run); 34b: with a synthetic owner the review carries 7 of 8 unusual rules (0 without) |
| `806778f` | `c758ed0` | Gate 34: stand-in gave 1 surprising verdict of 12 (not run); 34b registered: a synthetic owner with known unusual rules tests the mechanism ceiling |
| `d25e14e` | `f7d5e89` | Gate 34 amendment: the founder model plays the owner throughout (tests the mechanism, not real owners) |
| `f96b558` | `8534b29` | Gate 34 registered: the review with both halves fixed, on plans and payments |
| `0e9c455` | `b8dca68` | hive cloud tested on a real EC2 instance; two fixes from it |
| `a687de8` | `a5c8b88` | hive cloud: move a project's Hive to a cloud machine and run it from the phone; "build: ..." from Telegram |
| `0e3f6d0` | `2d26dbc` | Gate 33: a model of the founder predicts 35% of his surprising rules; it cannot stand in for him |
| `bb7e2dd` | `f90165b` | Gate 33 registered: can a model of the founder predict his verdicts, surprising ones included (leave one gate out) |
| `f6aa4d6` | `c42cf98` | hive listen: wake Hive any time on Telegram and change your mind; it finds and replaces the earlier ruling |
| `730838e` | `da5c06a` | Gate 32 not run: 5 surprising cases (6 required); how surprising an owner is depends on the area |
| `d53babc` | `807df3b` | Installable: pip install from GitHub gives a `hive` command; `hive doctor` checks a first-time setup |
| `3b48374` | `c03d2a8` | Gate 32 registered: both halves of the review working (scan and mark, then his way first); campaign selection and invitations |
| `5d37db4` | `6f1d5e1` | Gate 31: the one-line list found 8 of 9 surprising rules, but every marked decision was kept; kill fired |
| `5a76bb7` | `60ec869` | Gate 31 amendment before the build: 9 surprising, 3 ordinary (blind judge), founder confirmed 6/6 free-text readings |
| `5e1425c` | `0bdd6c5` | Gate 31 registered: Gate 30 rerun on a fresh feature with the new review (scan all, open first, rank by likely disagreement) |
| `de4aa80` | `640523a` | Owner review: scan every decision in one line, mark the ones to change, answer only those in full |
| `27d01d4` | `8f5ce4c` | Owner review after Gate 30: rank by likely disagreement, ask open first, check against earlier rulings |
| `52d466c` | `e3017ca` | Gate 30: first measured gain from the owner on surprising rules (+17 points), short of the +30 predicted |
| `6b3de1f` | `77fb9cd` | Gate 30 amendment before the build: 12 situations, cold probe, blind judge (6 surprising, 4 ordinary, 2 unclear), founder confirmed 6/6; one shared build |
| `d23049e` | `562a95d` | Bot: an early Done with no points sent is confirmed first (an accidental tap ended Gate 30 step 1) |
| `eb5c5c5` | `d38b73a` | Bot: open questions (hive telegram ask) and one-tap verdicts on situations (hive telegram verdicts) |
| `4e139bc` | `e7c9c34` | Gate 30 design registered: surprising cases fixed by a cold default probe; review with alternatives and suggestions off vs no owner |
| `e4a06b2` | `c7e26c6` | Owner review: disagreeing is one tap too (2-3 real alternatives per decision, Hive's pick starred) |
| `bff99f3` | `dbfa005` | Gate 29: kept rulings did not separate the arms (5/5 each; kill fired); memory halved the review list |
| `234dcd0` | `e6ba47a` | Gate 29 registered: do the owner's kept rulings carry into a related feature (memory vs no memory); surprising cases become Gate 30 |
| `71fecf0` | `059119d` | Memory of the owner's rulings across builds: never asked the same thing twice |
| `17f8b1f` | `e2db693` | Trial: the founder's phone review and fix round complete (437/437, 384 kept, $4.81, 32 min) |
| `e8a2fb3` | `f965ca7` | Catch contradictions in the owner's answers before anything reaches the builders |
| `b275ca9` | `e4e85ae` | Ask the bot for status anytime: "status" or "how's it going" gets a plain progress report |
| `b377ed4` | `afcc1ef` | Bot: capitalise the address at the start of a sentence ("Sir, a quick one...") |
| `49c8307` | `c973811` | The bot's voice: composed, courteous, a step ahead; the owner chooses how to be addressed |
| `cf9dc98` | `e85d6db` | Backup model for the plain-words step (e.g. NVIDIA NIM), used only when Claude can't be reached |
| `c396ae5` | `af55f41` | hive start: if the plain-words step fails, hand over as built and leave the review for hive morning |
| `b1fe79c` | `a3a34ca` | Never send the owner the raw assumption list: if the plain-words step fails, stop and say so |
| `d4df405` | `f7116bb` | Owner review: one tap with Hive's suggestion, undo, a final check, a chief-of-staff tone |
| `0f5a9b6` | `009d7a8` | BRAIN and queue: overnight mode, Telegram, plain-words review, first real hive start run |
| `c19dbe2` | `1a54bb8` | hive morning: greet with the goal's first line, not its raw heading |
| `ce01d2d` | `c98f135` | Owner review in plain words: context, an example, most important first; a proper greeting |
| `d140e3b` | `1d03de3` | Plan: M6 one-command flow and M7 owner phone done; M8 official bot planned for when customers arrive |
| `6300ee7` | `e1c01cf` | hive morning --phone: review an overnight build's assumptions on Telegram |
| `9f5520e` | `a9070ef` | Telegram: the owner answers questions and reviews assumptions from the phone |
| `fe4e292` | `cc627bd` | Trial: first real hive start run, overnight, works unattended (419/419, 384 kept, $2.49); 15 business assumptions |
| `61108e7` | `6b07a40` | Trial registered: the first real hive start run, overnight mode, on the company backend copy |
| `5691f5c` | `7515dae` | hive start --overnight and hive morning: build while the owner sleeps, review when back |
| `5d3da1e` | `f969a71` | Owner review shows business defaults only; stretched answers must be recorded (Gate 28 fixes) |
| `05771b2` | `6dda70a` | Queue: what a phone session may do for Gate 29 (collect the founder's cases into private Notion; no runs) |
| `c5ef320` | `986f748` | Gate 28: the assumption review had no room; questions tied again; a stretched answer backfired |
| `729be0c` | `d5503e0` | hive start: just type `hive`; one conversation from an idea to a tested branch |
| `46bcddf` | `1aa8390` | Gate 28 amendment before the run: 17 founder verdicts (2 documented, 15 head-only); ceiling rule |
| `8a43f4e` | `28663bd` | hive assume / hive review: the assumption review; Gate 28 registered |
| `d340a6e` | `5cf6052` | Gate 27: live founder questions did not beat a swarm that cannot ask (19/24 each); kill fired |
| `be47bdc` | `b7a5f78` | Gate 27 amendment before the run: 24 cases (14 documented, 10 head-only); founder verdicts on experimenter-proposed situations |
| `9f1c710` | `a195adb` | hive owner: friendlier question screen (numbered, wrapped, one choice per line); builders ask like talking to a busy founder |
| `805f202` | `ce542a0` | Gate 27 registered: acceptance cases from the founder's head, live founder vs a no-question control |
| `c38dc0a` | `c80ae76` | Plan: mark M5 done after Gate 26 |
| `782c317` | `80a2921` | Gate 26: the founder answered every plain-language question himself; 18/18 acceptance, 384/384 |
| `036ecbc` | `44f013f` | Gate 26 amendment before the run: acceptance cases from the company's documented spec; founder answers live |
| `05889ae` | `28ffa3c` | Gate 26 registered: founder-written acceptance cases and live answers, plain-language questions |
| `a8e88bc` | `b075b92` | Owner session: questions must be plain language for non-technical owners |
| `ad87eec` | `2ce56f8` | Gate 25 (Hive v1 M5): a real backlog feature in a real codebase, 23/23 hidden, 384/384 existing |
| `bf81e83` | `8561afd` | Gate 25 predictions: neutral wording (in-kind compensation) |
| `f610c4b` | `fb5e4d5` | Gate 25 (Hive v1 M5) registered: a real backlog feature in a real codebase, founder answering live |
| `bf62dd1` | `c13ab4a` | Hive v1 M4: the owner session (examples in every prompt, live questions, answers as tests) |
| `163b7aa` | `47f4756` | Hive v1 M3: hive run (bare upstream, one clone and prompt per worker, headless launch, cost log) |
| `f9dfda8` | `40ef23e` | Hive v1 M2: area claims (hive claim, hive areas) |
| `84d6df4` | `974d4a1` | Hive v1 M1 done: guard verified on a real Node.js backend; secrets refused, artifacts skipped, any branch |
| `bb32267` | `444a72d` | README: rewrite around the current evidence and Hive v1 |
| `5c75224` | `972b3a0` | Hive v1 M1: runner-agnostic guard (JUnit XML, content-keyed cache); lab note on the guard crash |
| `1087a5d` | `98407d4` | Move all gate folders into gates/ and update every path reference |
| `b31b63a` | `b48ed96` | Related work: what Hive can and cannot claim (first-pass literature check) |
| `d2f48e9` | `ad59251` | Gate 20: the founder's own examples beat agent-drafted ones on the real rules; documents settle what they cover |
| `9a5b470` | `a852b89` | Gate 24: Hive v1 end to end holds (95.0% vs 53.0% hidden at 6 workers, no breaking commits) |
| `4ff59b7` | `7fcf8d1` | Gate 20 amended before the run: add the company's own policy documents (team HTQ) |
| `6387bbf` | `2434a3c` | Gate 20 registered: the founder's own examples on the real rules (aggregates only) |
| `437aaf2` | `b06a078` | Gate 24 registered: Hive v1 end to end (owner tour + questions + content-keyed guard, 6 workers) |
| `330c3b2` | `168b12d` | Gate 23: first attempt aborted at the usage limit; content-keyed cache hit 337 of 338 (unscored) |
| `56953c0` | `32ecd38` | Gate 23 registered: guard cache keyed by code content instead of commit |
| `3ffecb5` | `2bf9d1e` | Gate 22: cached guard 0.72x again; hits stuck at 58% because half of main's commits are locks |
| `86430db` | `dbfd56c` | Gate 22: first attempt aborted at the account's usage limit; to be rerun from scratch |
| `4f5dc4e` | `cf5a3dc` | Gate 22 registered: store-before-push guard as a held-out test of Gate 21's finish model |
| `636076b` | `84b01ef` | Gate 21: CPU per guard check sets the finish (3.5 -> 12.1 min at 4 CPUs); cached guard 0.84x |
| `c757c39` | `00d7173` | Gate 21 registered: cached guard vs Gate 3's guard on a CPU-limited container |
| `e47f7e8` | `076911f` | Gate 10: largest-first claiming does not cut the finish (4.3 vs 3.5 min); the guard's CPU cost does |
| `f1f7a15` | `613be5f` | Gate 10 registered: largest-first claiming vs Gate 3's claiming, 12 workers each, same machine |
| `84dd58d` | `761406b` | Gate 18: owner-confirmed examples carry a real company's intent (26.0% -> 64.8%; with questions 78.0%) |
| `1c1f661` | `f427dc4` | Gate 18 registered: the decision tour on a real company's rules (aggregates only) |
| `2ce1852` | `179f835` | Gate 17: documented owner 93.8% vs listing owner 98.2% on the same rules; gap at unwritten decisions |
| `d55cd46` | `654f2fb` | Gate 17 registered: documented owner vs listing owner on the same rules, fair copy rule |
| `b03bfd3` | `84491be` | Gate 16: stacked documented-owner interface reaches 83.2%; each layer adds; 90% target missed |
| `7d04573` | `e009afe` | Gate 16 registered: the stacked interface (handbook + extracted tour + builder questions) |
| `3d19655` | `696928c` | Gate 15: a tour built from a policy handbook keeps 0.75 of the tour gain (80.6% vs 92.6%) |
| `c04ed1c` | `2259735` | Gate 15 registered: can a decision tour be built from a policy handbook? |
| `5d83b0c` | `a71dfe3` | Gate 14: the decision tour replicates (42.4% -> 95.6%); contrast examples do not help (90.8%) |
| `14d5ec9` | `9bca48d` | Gate 14 registered: decision tour with contrast pairs, replicated on a new rule-giver |
| `e99885d` | `1006b45` | Queue: handoff after Gate 13 |
| `a896fee` | `f8403a5` | Gate 13: the owner's decision tour beats builder questions (89.4% vs 67.2%); with both, 95.2% |
| `6ba9283` | `ea18f07` | Gate 13 registered: the owner's decision tour vs builder-chosen questions |
| `fb3ac4d` | `1f7ff98` | Gate 12: more decisions weaken each question, but a 21% floor of unprobed decisions caps questions |
| `23cbe83` | `403b31b` | Gate 12 registered: does question saturation track hidden decisions? |
| `1ab8cc2` | `1bc7bdb` | Gate 11: spread beats blocks of 3 (1.25x), but Gate 8's p-law fails (p = 0.35); law withdrawn |
| `20af7c5` | `6510aa3` | Gate 11 registered: spread vs blocks of 3, stratified by headroom; run_gate.py two-stage mode |
| `0314dec` | `a7d4303` | Gate 8: questions cause the gain again (+29.4); R3 failed, blocks-of-3 withdrawn; one law fits Gates 6 and 8 |
| `a43088d` | `bab6a4e` | Lab: run any gate in one command from any Claude Code session; Gate 8 registered |
| `a92a014` | `9904e2e` | Docs: drop company byline |
| `7aedeaf` | `54c2f17` | Gate 7: a real company's rules as product owner; answers lift hidden correctness 32.8% -> 49.6% |
| `b953a53` | `d9a4aea` | Gate 7: register predictions for a human product owner before the rules exist |
| `06dc54f` | `260d7e7` | Gate 6: questions cause the gain; one question per function buys little |
| `43d998f` | `80be8ed` | Gate 6: register predictions and random assignment before the rules exist |
| `6dd0f79` | `2e47ee6` | README: Gate 5 findings and layout |
| `d00eab2` | `ab66674` | Gate 5: asking about defaults first did not beat free asking (62.2% vs 67.0%) |
| `5f1acd4` | `d3b1ade` | Gate 5: register predictions, team prompts and rule-giver brief before the rules exist |
| `44bc870` | `cbb0346` | Gate 4: planned questions did not beat free questions (76.4% vs 76.8%) |
| `571bf21` | `e4299f7` | Gate 4: register predictions before launch (planned vs free questions) |
| `fb365c8` | `beef508` | Gate 3 intent test: 58% / 87% / 98% hidden at 0 / 30 / unlimited questions |
| `54ffd42` | `97dc000` | CLAUDE.md: point every session at BRAIN.md and the lab rules |
| `7f52ae5` | `af2a2a5` | Shared brain (BRAIN.md), Hive v2 doc, Gate 3: protocol v2 and scale runs |
| `4feb718` | `c386f0d` | Gate 2 results: 2/6/12-worker swarms, predictions scored, histories and hidden scores |
| `88d8148` | `7fa8ba6` | Hive research: real-repo analysis, simulator v2, Gate 0 replay, Gate 1 swarms, Gate 2 setup |
