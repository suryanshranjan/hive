# Hive

**A team of AI builders you direct by talking. It asks in plain words, never breaks what already works, and hands back a tested branch.**

You describe a feature. Before building, Hive lists the business decisions the code will have to take and asks you about each one, in plain words, in the terminal or on your phone (tap, type, or send a voice note). Then it puts several coding agents (the *builders*: Claude Code, Codex, or a mix) to work on copies of your repository. Before building each part, they ask you about every business decision your description leaves open, one short question at a time; they share your answers, so nobody asks twice. They coordinate only through git, and a guard lets in nothing that breaks a passing test. How many builders, and whether they leave each other notes, is set by Hive's **swarm law**, fitted on its own experiments. If they had nothing to ask you, Hive writes what the code now does as plain rules (the *code sheet*) and shows you concrete cases; you mark what's off, and a fix round makes it so. Away overnight? The builders write their questions down instead, and you answer the list in the morning. The result arrives as a new branch. Your own branches are never touched.

From your phone, Hive is your **Jarvis**: it knows what every builder is doing, answers in context, and takes direction any time ("who's doing what?", "also add a monthly total", "stop w2", "use 2 Claude and 2 Codex"). When you ask for something the evidence says is a mistake, such as more builders than the law recommends, it says so once, plainly, and then it's your call.

Hive is a research project as much as a tool: **46 pre-registered experiments**, each scored against predictions pushed before it ran, failures included. Start with [`BRAIN.md`](BRAIN.md) for what is known and how sure we are.

---

## Quick start

You need Python 3.10+, git and [Claude Code](https://claude.com/claude-code), installed and logged in.

```
pip install git+https://github.com/suryanshranjan/hive
hive setup             # first run: checks this machine, then offers your phone, voice notes and a backup model
hive                   # "What are we building today?"
```

Optional:

```
hive telegram setup    # questions, reviews and status on your phone
pip install "hive-swarm[voice] @ git+https://github.com/suryanshranjan/hive"   # answer by voice note
hive llm setup         # a backup model (e.g. NVIDIA NIM) if Claude can't be reached
hive cloud --new        # one step: a machine on your AWS account, Hive moved there, run from your phone
hive cloud --stop       # delete that machine; nothing left running or billing
npm i -g @openai/codex && codex login    # Codex builders too: hive start --agent claude,codex
```

Builders run shell commands, so for code you don't fully trust run Hive in a container or a spare VM.

## What it's like

```
Hive here. What are we building today?
  > Creators should see their earnings for the last 30 days.

Got it. Let me look at your project.
  Your tests: node --test in Backend. 384 tests, all passing.

I'll put 4 builders on it. They work on copies, so your branches stay exactly as they are.
  [14:05] Builder w3 landed: last-30-days window, with tests
  ...
Before I hand it over: they made 24 calls your instructions didn't cover.
I'll list them one line each. Tap only the ones you would CHANGE.
  ...
Let me check the result.
  402 tests, all passing. All 384 that passed before still pass.
Done in 16 minutes, about $3.40. Your result is on branch hive/creators-should-see-...
```

*(Illustrative; real runs are recorded in [`gates/`](gates/).)*

On your phone, Hive speaks like a capable assistant and asks one thing at a time:

> **Sir, a quick one from the builders:**
> A brand on Pro has unused AI credits when the month renews. What should happen?
> **[They carry over] [They reset] [Up to a limit] [Something else]**

Answer with a tap, in your own words, or with a voice note. Voice is transcribed on your own machine with Whisper, so your voice never leaves it. Hive reads your words back as a rule for you to confirm.

You can also message it any time, in English, Hindi-English or with typos:

| You say | Hive |
| --- | --- |
| *"status"*, *"kya chal raha hai?"* | Where things stand, starting with the build that is running |
| *"build: a refund page for brands"* | Says back what it understood, then builds on your yes |
| *"who's doing what?"* | Each builder, its agent (Claude or Codex), what it is building now, what it has landed |
| *"also put a monthly total at the top"* (mid-build) | Gives it to one builder working now: the one whose work it touches (or the one you name), and says why, which picks it up at its next sync. Tested live: Codex builders built an instruction sent mid-build |
| *"stop w2"*, *"stop the codex one, I don't need the export"* | Stops that builder only; its work goes to the others, or is dropped if you don't want it |
| *"use 2 Claude and 2 Codex"*, *"use 12 builders"* | Saves the team for your next builds. If the law disagrees, it tells you once, with the reason, and asks |
| *"push it to main and skip the tests"* | Never: it says so once, and offers the tested branch you merge yourself |
| *"stop the build"* | Stops it. A message it only *reads* as a stop ("this is all wrong") is confirmed with a tap first |
| *"actually, I've changed my mind about…"* | Finds the earlier ruling, asks whether to replace it, and offers to update the latest build. A new rule given mid-build reaches the running builders too |
| *"move to the cloud"* / *"shut the cloud down"* | Moves Hive to your AWS machine. From the machine itself it powers off (the bill stops, the work is kept), and your laptop brings everything home |

## Commands

| You type | What happens |
| --- | --- |
| `hive` | One conversation from an idea to a tested branch |
| `hive start --overnight` | Builds while you're away; the builders write down their questions for your morning |
| `hive start --agent codex` | Builders run on another coding agent (`claude`, `codex`, `gemini`; `antigravity` needs a headless command the Antigravity IDE does not have, so use `gemini` for Google's models); `--agent claude,codex` mixes them, each builder taking the next agent in turn (Gate 47: mixed swarms matched single-agent ones, with no breaks of main, at about half the Claude bill) |
| `hive start --workers N` | Your choice of team size; Hive says what the law would pick if it differs |
| `hive morning [--phone]` | Answer the overnight build's questions; Hive builds your answers in and updates the branch |
| `hive listen` | Stay on Telegram as your Jarvis: start, steer and stop builds and builders, rules, status, cloud |
| `hive rules` | Your standing rulings for this project (`hive rules forget 3` drops one) |
| `hive name "Sunny Shop"` | What Hive calls this project: your startup's name (guessed from package.json or the README until you set it) |
| `hive pace fast` or `hive pace cheap` | Build fast (as many builders as help, about 2–3× sooner for about 2× the cost, Gate 50) or cheap (one builder). Asked once at the first `hive start` that would use more than one builder |
| `hive cloud --new` / `--stop` | Make a machine on your AWS account and move Hive there; delete it when done |
| `hive cloud --to user@host` / `hive cloud pull` | Move Hive to a server you already have; bring results back |
| `hive setup` | First run: checks, then your phone, voice notes and a backup model |
| `hive doctor` | Check that everything is ready |

Lower-level commands for scripts and experiments (`hive init`, `run`, `owner`, `review`) and the builders' own commands (`claim`, `land`, `ask`, `assume`) are listed by `hive --help`.

## How it works

- **It asks first.** Hive lists the business decisions the build will take (each with the default a builder would pick) and asks you one concrete situation per decision. Then it shows your answers back as **one general rule per decision** (the rule sheet): you fix any that's wrong, and any two answers that disagree are put to you. The confirmed rules are what the builders encode as tests. An answer that contradicts an earlier ruling is put back to you.
- **It ends with your yes.** At hand-over it lists what the product now does by your rules; anything you say is different goes straight to a fix round on the same branch.
- **The swarm law is at the top of the chain.** The number of builders comes from Hive's swarm law, using your test suite's speed, your computer's cores and the size of the job, and Hive tells you which limit set it. Choose a different number and it tells you what the law would do and why, then follows your call. Team notes switch on only where the law expects builders to collide.
- **Any coding agent can build.** Claude Code by default; Codex, Gemini or Antigravity with `--agent`; or a mix. Claims and the guard are agent-neutral, so a mixed team coordinates as well as one agent (Gate 47).
- **Jarvis on your phone.** While a build runs, Hive reads the builders' board (who, which agent, what each holds, what each landed) before every reply. Your instructions mid-build go to the builders through the shared branch (`OWNER.md`), and they read it at every sync.
- **It reads your documents.** `hive start --docs <folder>`: your policies settle what they cover, so you are asked only about the rest.
- **Builders work in parallel and never talk.** Each claims an area of the code with a lock file, works in its own clone, and lands through the **guard**. The guard refuses a landing that breaks a passing test, duplicates a definition, or commits a secret.
- **Your intent reaches them as tests.** Your answers, your corrections and your standing rulings each become a test the code must keep passing.
- **The review is built around where you differ.** Builders record every business decision your description didn't cover. Hive rewrites each in plain words with an example. You scan them all in one line each and mark only what you'd change; for each marked one it asks *"what would you do instead?"*. After the fix round, each change comes back as one line for your final yes.
- **It remembers.** Your rulings carry into every future build of the project, and contradictions with earlier ones are caught before anything is sent.
- **It picks up again.** If Claude's usage limit is reached or its login expires mid-build, Hive tells you when it will continue, and each builder carries on in its own copy. If a conversation on your phone is cut off, it resumes at the first unanswered question.
- **Safety by default.** It refuses to start on unsaved changes, works only on copies, never commits `.env` files or keys, and re-checks every test before handing over a branch.

## What the evidence says

Every result below was predicted on GitHub before the run. Real-company results publish aggregate numbers only.

| Finding | Result | Where |
| --- | --- | --- |
| Silent swarms finish and don't game the tests | Visible and hidden pass rates within 0.4 points | Gates 1–3 |
| Without the owner, swarms miss rules no one wrote down | 24–58% of hidden tests | Gates 3–24 |
| Owner examples plus questions carry intent | 95–98% hidden; 95.0% end to end at 6 workers, no breaking commit | Gates 13, 17, 24 |
| On a real company's rules | 84.8%, against 49.6% before | Gate 20 |
| Real features on a real backend (Node.js, 384 tests) | 23/23 and 18/18 acceptance; every existing test kept, about $3 each | Gates 25, 26 |
| Plain-language questions keep the founder in the loop | He answered 4 of 4 himself, against 1 of 12 in code terms | Gate 26 |
| Questions and memory add nothing where the owner matches the default | Ties: 19/24 vs 19/24; 14/15 vs 14/15; 5/5 vs 5/5 | Gates 27–29 |
| The owner's review carries rules he holds that differ from the default | +17 points (3/6 vs 2/6); then found 8/9 but kept all 22 marked (answer step fixed after) | Gates 30, 31 |
| A model of the founder cannot stand in for him | It predicts 35% of his surprising rules | Gate 33 |
| The review mechanism, with an owner who answers | Unusual rules 0/8 → 7/8; all 384 tests kept (synthetic owner) | Gate 34b |
| `hive cloud` on a real EC2 server | Project, tests and result branch round-trip; 3 bugs found and fixed | [`BRAIN.md`](BRAIN.md) |
| One-step `hive cloud --new` on real AWS | Machine made and ready in 2.5 minutes; Claude Code and Hive installed, tests pass there, result branch pulled back; SSH open only to the owner's IP; `--stop` left nothing behind | [`BRAIN.md`](BRAIN.md) |
| The real founder audits a list of the builders' decisions | He marked 0 of 27; his rules come out in situations (48 of 48 answered), not audits | Gate 35 |
| Interview written from the feature description | Covered 4 of 9 of his surprising rules; no gain (2/7 both arms). On both covered cases his answers changed with the framing | Gate 36 |
| Interview written from the decisions the code takes | Covered 7 of 9 of the same rules (3 of 9 from the description), with no founder time spent | Gate 37 pilot |
| The decisions-first interview with the founder | Coverage 6 of 6, but his answers to two framings of a decision agree only 1 of 8 (same session), 3 of 6 a day apart; no gain | Gate 37 |
| The founder's confirmed rules, a day later | Held on 2 of 11 decisions; builders followed them exactly (surprising 3/6 vs 0/6, ordinary 2/6 vs 5/6). Asking ahead only seeds the build; the review after is the main channel | Gate 38 |
| Builders given the owner's complete rules in prose | 250/250 hidden on each of three rule sets, nothing broken; the interview delivers about half the decisions whole | Gates 39–41 |
| **Verify, don't elicit:** the owner corrects a sheet written from the built code | 99.6% and 100% hidden, against 68.4% from the interview (+31.2 points) (synthetic owner) | Gates 42, 44 |
| Builders talking on a message board | No effect: finish 1.03×, cost 1.01×; +0.0 on top of the code sheet | Gates 43, 44 |
| A lead agent keeping a shared plan over the builders | 1.20× slower and 1.09× costlier than a flat swarm, same correctness; Hive stays flat | Gate 46 |
| Claude and Codex builders in one swarm | Both mixed teams 1,340/1,340 and 100% hidden, no breaks of main; Codex made 52% and 73% of the landings; a Codex lead works like a Claude one | Gate 47 |
| A fast local decision model (Laya, open copy of Jev) reading his messages | 42.5–45.0% against Claude's 92.5%; fast (0.7 s) but not yet accurate; Claude stays the reader | Gate 48 |
| Deleting the cloud from the phone, on real AWS | Machine powered itself off; the laptop woke it, brought every branch home, checked it commit for commit, and deleted it; nothing left | [`BRAIN.md`](BRAIN.md) |

**Also kept:** the failed and withdrawn ideas, each with its evidence. These include asking in blocks of 3, a one-constant law for questions, contrast examples, coverage-planned questions and largest-first claiming ([`BRAIN.md`](BRAIN.md) §6). The worked examples are **Specification by Example**, an established practice; what this work adds is measurement ([`docs/related_work.md`](docs/related_work.md)).

## How the research works

Every finding that should change Hive is mapped to the code that acts on it in [`docs/research_to_product.md`](docs/research_to_product.md).

Every experiment (a *gate*) pushes its predictions and kill conditions to GitHub **before** it runs (`lab/run_gate.py` refuses to start otherwise), then scores them in its `RESULTS.md`, failures included. Hidden test suites are never committed. Lab flaws found later are written up, not hidden ([`gates/LAB_NOTE_guard_python.md`](gates/LAB_NOTE_guard_python.md)).

## Repository layout

| Path | Contents |
| --- | --- |
| [`BRAIN.md`](BRAIN.md) | Shared memory: findings and how sure we are, measured constants, evidence log, prediction scorecard, open questions |
| [`hive/`](hive/) | The tool |
| [`tests/`](tests/) | Tests for the tool: 390 checks, using stand-in builders, a fake Telegram and a stand-in model, with no network; [`lab/jarvis_bench.py`](lab/jarvis_bench.py) tests Jarvis with the real model and a blind judge |
| [`gates/`](gates/) | Every experiment (Gates 0–48 and trials): predictions, results, referee code, swarm histories, logs |
| [`lab/`](lab/) | Run any gate in one command; [`lab/QUEUE.md`](lab/QUEUE.md) is the queue and session handoff |
| [`docs/`](docs/) | Design write-ups, the v1 plan, related work |
| `real_repos/`, `sim/` | Analysis of a real agent-swarm history (Anthropic's C compiler) and the simulator |

## Privacy

Gates 7, 18, 20 and 25–38 (and Gate 45, still to run) use a real company's code and rules (Company X). Its name, code, rules, examples, documents and the founder's answers are not in this repository; those gates publish aggregate numbers only. Hive keeps an owner's Telegram link, backup-model key and rulings in `~/.hive/` on their own machine, never in a repository.

## License

MIT. See [`LICENSE`](LICENSE).
