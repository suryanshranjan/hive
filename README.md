# Hive

**A team of AI builders you direct by talking. It asks in plain words, never breaks what already works, and hands back a tested branch.**

You describe a feature. Hive puts several coding agents (the *builders*) to work on copies of your repository. They coordinate only through git, and a guard lets in nothing that breaks a passing test. When the builders hit a decision only you can make, Hive asks you in plain words, in the terminal or on your phone. At the end it shows you the calls they made, you correct the ones you would make differently, and Hive delivers the result as a new branch. Your own branches are never touched.

Hive is a research project as much as a tool: **35 pre-registered experiments**, each scored against predictions pushed before it ran, failures included. Start with [`BRAIN.md`](BRAIN.md) for what is known and how sure we are.

---

## Quick start

You need Python 3.10+, git and [Claude Code](https://claude.com/claude-code), installed and logged in.

```
pip install git+https://github.com/suryanshranjan/hive
hive doctor            # checks this machine and project; says how to fix anything missing
hive                   # "What are we building today?"
```

Optional:

```
hive telegram setup    # questions, reviews and status on your phone
hive llm setup         # a backup model (e.g. NVIDIA NIM) if Claude can't be reached
hive cloud --to user@host   # run Hive on a server and drive it from your phone
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

You can also message it any time: *"status"*, *"build: a refund page for brands"*, or *"actually, I've changed my mind about…"*. Hive finds the earlier ruling, asks whether to replace it, and offers to update the latest build.

## Commands

| You type | What happens |
| --- | --- |
| `hive` | One conversation from an idea to a tested branch |
| `hive start --overnight` | Builds without asking anything; you review the next morning |
| `hive morning [--phone]` | Check an overnight build's decisions; Hive fixes what you correct |
| `hive listen` | Stay on Telegram: change your mind, start builds, ask for status |
| `hive rules` | Your standing rulings for this project (`hive rules forget 3` drops one) |
| `hive cloud --to user@host` / `hive cloud pull` | Move a project's Hive to a server; bring results back |
| `hive doctor` | Check that everything is ready |

Lower-level commands for scripts and experiments (`hive init`, `run`, `owner`, `review`) and the builders' own commands (`claim`, `land`, `ask`, `assume`) are listed by `hive --help`.

## How it works

- **Builders work in parallel and never talk.** Each claims an area of the code with a lock file, works in its own clone, and lands through the **guard**. The guard refuses a landing that breaks a passing test, duplicates a definition, or commits a secret.
- **Your intent reaches them as tests.** Your answers, your corrections and your standing rulings each become a test the code must keep passing.
- **The review is built around where you differ.** Builders record every business decision your description didn't cover. Hive rewrites each in plain words with an example. You scan them all in one line each and mark only what you'd change; for each marked one it asks *"what would you do instead?"*. After the fix round, each change comes back as one line for your final yes.
- **It remembers.** Your rulings carry into every future build of the project, and contradictions with earlier ones are caught before anything is sent.
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
| **Open:** the real founder with the fixed review | In progress | Gate 35 |

**Also kept:** the failed and withdrawn ideas, each with its evidence. These include asking in blocks of 3, a one-constant law for questions, contrast examples, coverage-planned questions and largest-first claiming ([`BRAIN.md`](BRAIN.md) §6). The worked examples are **Specification by Example**, an established practice; what this work adds is measurement ([`docs/related_work.md`](docs/related_work.md)).

## How the research works

Every experiment (a *gate*) pushes its predictions and kill conditions to GitHub **before** it runs (`lab/run_gate.py` refuses to start otherwise), then scores them in its `RESULTS.md`, failures included. Hidden test suites are never committed. Lab flaws found later are written up, not hidden ([`gates/LAB_NOTE_guard_python.md`](gates/LAB_NOTE_guard_python.md)).

## Repository layout

| Path | Contents |
| --- | --- |
| [`BRAIN.md`](BRAIN.md) | Shared memory: findings and how sure we are, measured constants, evidence log, prediction scorecard, open questions |
| [`hive/`](hive/) | The tool |
| [`tests/`](tests/) | Tests for the tool: about 140 checks, using stand-in builders, a fake Telegram and a stand-in model, with no network |
| [`gates/`](gates/) | Every experiment (Gates 0–35 and trials): predictions, results, referee code, swarm histories, logs |
| [`lab/`](lab/) | Run any gate in one command; [`lab/QUEUE.md`](lab/QUEUE.md) is the queue and session handoff |
| [`docs/`](docs/) | Design write-ups, the v1 plan, related work |
| `real_repos/`, `sim/` | Analysis of a real agent-swarm history (Anthropic's C compiler) and the simulator |

## Privacy

Gates 7, 18, 20 and 25–35 used a real company's code and rules (Company X). Its name, code, rules, examples, documents and the founder's answers are not in this repository; those gates publish aggregate numbers only. Hive keeps an owner's Telegram link, backup-model key and rulings in `~/.hive/` on their own machine, never in a repository.
