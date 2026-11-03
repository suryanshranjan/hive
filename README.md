# Hive

**Run your product from your phone. Tell Hive what you want for the business; it works out what to change, builds it with a team of AI coding agents, shows you, and hands it to your engineer. Nothing breaks what already works, and nothing goes live without review.**

Hive is a founder's assistant, in the manner of J.A.R.V.I.S. You talk to it on Telegram in plain words, Hindi-English, voice notes or pictures:
- **Business goals:** "I want more creators signing up this month." Hive reads your product, finds what holds your customers back, and comes back with a short plan in your words. On your yes it builds each step and sends you screenshots.
- **Particular tasks:** "add an invite page".
- **Technical instructions,** if you're technical yourself: "cache /products in Redis, 60 s TTL". It answers in your terms.
- **Pictures:** "make it like this".
- **Complaints:** "a customer says…"

Hive asks you only what only you can decide. It builds on copies of your code, checks every test, and arrives as a pull request for your engineer. When it's merged, "put it live" puts it live, and "undo that" takes anything back.

Hive is a research project as much as a product: **107 pre-registered experiments** (*gates*), each scored against predictions pushed before it ran, failures included. Start with [`BRAIN.md`](BRAIN.md) for what is known and how sure we are.

---

## Quick start

You need Python 3.10+, git, and [Claude Code](https://claude.com/claude-code) installed and logged in.

```
pip install git+https://github.com/suryanshranjan/hive
hive setup                                   # checks, your phone (Telegram), screenshots, numbers, where it lives; then live
hive up --repo https://github.com/you/your-product   # or: fetch your code, and Hive is live on your phone
```

`hive setup` connects Telegram in two minutes. It offers screenshots, your business numbers and your hosting service, then starts listening and says hello on your phone. After that, everything happens in Telegram. In a terminal, `hive` alone starts one conversation from an idea to a tested branch.

**Optional extras:**

```
pip install playwright && playwright install chromium   # screenshots of what was built, on your phone
pip install "hive-swarm[voice] @ git+https://github.com/suryanshranjan/hive"   # answer by voice note (Whisper, on your machine)
npm i -g @openai/codex && codex login       # Codex builders too: "use 2 Claude and 2 Codex"
hive deploy setup vercel                     # where it lives: vercel, netlify, railway, azure, fly, render, or custom
hive numbers setup --url https://.../stats.json   # your numbers, so Hive can tell you whether a change worked
hive brain add docs/                         # your policies, FAQs and notes, so Hive knows the business
hive cloud --new                             # a machine on your AWS account; Hive keeps working while your laptop sleeps
```

Builders run shell commands, so for code you don't fully trust, run Hive in a container or a spare VM.

## What it's like

A real exchange from the end-to-end rehearsal (Gate 107), abridged:

> **You:** I want more creators signing up this month.
>
> **Hive:** 🔎 On it, sir. Let me look at your product with that in mind.
>
> **Hive:** ❓ Before I plan it, one thing your product can't tell me: is the ₹500 first-deal bonus open to every new creator?
>
> **Hive:** 🧭 Here's what I see, sir. A creator can only reach sign-up from a small footer link, on a home page that never mentions earning; then they face 9 required fields, bank details included, before they see any deal. What I'd do:
> 1. **A shorter sign-up form**
> 2. **A home page that talks to creators**
> 3. **Make the invite reward easy to see**
>
> All of it: about $1.50.
> **[🚀 Yes, do it all] [Just the first] [Not now]**
>
> **Hive:** ✅ Step 1 of 3 done: A shorter sign-up form. *(screenshot of the sign-up page)*
> … ✅ Step 3 of 3 done. 🎉 That's the plan done, sir. 22 tests, all passing. Tell me what's off, or say *ship it*.
>
> **You:** ship it → ✅ Sent to your engineer (a pull request with screenshots, what changed and your words)
>
> **You:** put it live → 🚀 Your engineer has merged it. I'll run every test first. ✅ It's live, sir.

**What you can say:**

| You say | Hive |
| --- | --- |
| *"I want more sign-ups"*, *"sales are low"* | Reads your product and plans 2-4 changes in your words, each grounded in what it saw. It first asks the one thing the product can't show. On your yes it builds them step by step, showing each |
| *"build: an invite page"*, *"add a refund page"* | Says it back in one short line, with the price ("about $0.80"), then builds on your yes |
| *"cache /products in Redis, 60 s TTL"* | A technical instruction is taken as it is: "👍 Yes, let's do it", restated precisely, with at most two normal engineer's questions. From then on it speaks your language |
| A picture + *"make it like this"* | Changes the latest build to match, then sends before and after. In testing a picture matched 18 of 18 times, words 13 of 18 |
| *"show me"* | Screenshots at phone size of the pages that changed |
| *"send me a link"* | The build at its own address, to try on your phone; your live product is untouched |
| *"ship it"* | A pull request for your engineer: screenshots, what changed, your words, the test results, the cost |
| *"put it live"* | Only once your engineer has merged it; every test runs on your main version first |
| *"undo that"* | Whatever is most recent, after your yes: a build running stops; an unsent one is set aside; a pull request is withdrawn; live goes back to the version before |
| *"a customer says the sign-up button doesn't work"* | Reads the code and tries the case. Either it's one of your rules at work (change it in a message), or a fault, fixed in one tap |
| *"what's new?"* (and every morning, unprompted) | The brief: what needs you, how your numbers moved since what Hive did, what landed, what customers hit, what it cost |
| *"we had 120 sign-ups this week"* | Kept as a reading, beside what Hive did, so the brief can say "up 18% since the shorter form went to your engineer" |
| A document (policy, FAQ, deck as PDF) | Read; the lasting facts are kept for every plan and answer, and rules it plainly states become your rules |
| *"we're on Vercel"* | Remembered: previews and going live use it (Vercel, Netlify, Railway, Azure, Fly, Render, or your own commands) |
| *"set my budget to $50 a month"* | Hive asks before anything would go past it |
| *"how do refunds work?"* | Answered from your code, trying the case in a throwaway copy |
| *"actually, refunds go to store credit"* | Finds the earlier ruling, asks whether to replace it, updates the latest build |
| *"status"*, *"who's doing what?"*, *"stop w2"*, *"use 2 Claude and 2 Codex"* | Where things stand; each builder and its agent; one builder stopped; your team for the next builds (the swarm law says once if it disagrees) |
| *"skip the tests and push it to main"* | Never. It says so once, and offers the safe way |

## Commands

| You type | What happens |
| --- | --- |
| `hive setup` | First run: checks, Telegram, voice, screenshots, numbers, your host; then live on your phone |
| `hive up [--repo <address>]` | Live on your phone now, listening in the background; `--repo` fetches your code first |
| `hive` | One conversation in the terminal, from an idea to a tested branch |
| `hive listen` | Stay on Telegram as your assistant (what `hive up` starts) |
| `hive start --overnight` | Builds while you're away; the builders write their questions down for your morning |
| `hive start --agent claude,codex` / `--workers N` | Builders on other agents (`claude`, `codex`, `gemini`), mixed in turn; your choice of team size |
| `hive morning [--phone]` | Answer the overnight build's questions; your answers are built in |
| `hive deploy setup <host>` / `preview` / `status` | Where your product lives; a preview address of the latest build |
| `hive numbers [setup --cmd/--url/--file \| add name=value]` | Your business numbers, as they move |
| `hive brain add <file or folder>` | Teach Hive your business from documents |
| `hive rules` (`hive rules forget 3`) | Your standing rulings for this project |
| `hive name "Sunny Shop"` | What Hive calls your project |
| `hive pace fast` / `cheap` | Speed against cost (about 2-3× sooner for about 2× the cost) |
| `hive cloud --new` / `--stop` | A machine on your AWS account, and Hive moved there; deleted when done |
| `hive doctor` | Check that everything is ready |

The lower-level commands for scripts and experiments (`init`, `run`, `owner`, `review`) and the builders' own (`claim`, `land`, `ask`, `assume`) are in `hive --help`.

## How it works

- **Your business first.** A business goal goes to a planner that reads your product in a throwaway copy. It splits the goal into the questions that decide it, and proposes only steps grounded in something it saw, so a step that cites nothing is dropped. It asks the one thing the product can't show ("do you already give new creators anything?"). Steps are built one after another on one branch, each shown to you.
- **It asks only what only you can decide.** Business edge cases come as concrete situations ("a refund half paid by points: back to the card, or as points?"), and plain facts as plain questions. Your answers become rules, encoded as tests. Questions never invent facts about your business.
- **Your work adds up.** A new request builds on top of your latest unmerged build, so everything reaches your engineer as one pull request (Gate 107).
- **A safety net when there are no tests.** Most founders' projects have few tests. Hive first writes tests that pin how the product behaves today, then builds, so "every test passes" means something.
- **A look is shown, not quizzed.** A change to how a page looks gets one builder, no questions, and screenshots as the review. It can take the look of a site you name (never its logo, name or words).
- **The swarm law sets the team.** How many builders, from your tests' speed, your machine and the job's parts. Choose differently and it tells you once what the law would pick.
- **Builders never talk; a guard keeps the peace.** Each claims an area with a lock file, works in its own clone, and lands through the guard. The guard refuses anything that breaks a passing test, duplicates a definition or commits a secret. Claude, Codex and Gemini builders mix in one team (Gate 47).
- **Checked before every delivery.** The goal's stated interfaces (Gate 84), your own examples run through the product's functions (Gate 103), and every test.
- **It remembers.** Your rulings, your business notes and your documents carry into every later build and answer. Contradictions with an earlier ruling are put to you.
- **It speaks first.** A morning brief at your local time, a builder stuck for 20 minutes, a step done, a build that stopped, always with the reason in plain words.
- **Hard limits, whatever is asked:** it never changes your main version, never skips the tests, and never puts live a build your engineer hasn't merged.

## What the evidence says

Every result below was predicted on GitHub before the run. Real-company results publish aggregate numbers only. Most of the recent gates use a synthetic owner who answers from a written policy, on mock products. The founder session on a real product is the next test.

| Finding | Result | Where |
| --- | --- | --- |
| Silent swarms finish and don't game the tests | Visible and hidden pass rates within 0.4 points | Gates 1-3 |
| Without the owner, swarms miss the rules no one wrote down | 24-58% of hidden tests | Gates 3-24 |
| Owner examples and questions carry intent | 95-98% hidden | Gates 13, 17, 24 |
| On a real company's rules and backend | 84.8% against 49.6%; real features 23/23 and 18/18, every existing test kept | Gates 20, 25, 26 |
| The real founder audits lists poorly but answers situations | Marked 0 of 27 in a list; answered 48 of 48 situations | Gates 35-38 |
| The owner corrects a sheet written from the built code | 99.6% and 100% hidden, against 68.4% from the interview | Gates 42, 44 |
| One agent that asks vs Hive's hand-over | The asking agent won by 21-30 points; Hive's builders now ask first | Gates 66, 68 |
| Overnight questions answered in the morning | 94.2% against 75.0% for a morning hand-over | Gate 70 |
| Claude and Codex builders in one swarm | 1,340/1,340, 100% hidden, no breaks of main | Gate 47 |
| A split swarm (one builder owns the owner's decisions) | One agent's accuracy (90.0 vs 86.5%) in 0.45× the time, at 1.95× the cost | Gates 74, 75 |
| Real Django issues | One builder 8/10; `hive start` 8/10 at 15× the cost. On technical goals Hive now acts like one builder | Gates 86, 89 |
| Reliability and owner load | pass^5 held (10 of 10); owner prompts 55 → 23 per feature | Gates 93-104 |
| Memory against silent drift; the owner's examples checked before delivery | 27-29 of 29 with memory (20, 29, 17 without); the check caught a refund sent the wrong way | Gates 101, 103 |
| His picture vs his words for a look | 18/18 against 13/18 measured checks; a blind judge preferred the picture 3 of 3; same cost | Gate 105 |
| Give it the business, not the task | 8 of 9 planted problems found and built from a goal alone, 4 owner messages, no technical words; a simulated customer panel (MiroFish's idea) added nothing | Gate 106 |
| A fresh founder end to end (14 steps on the phone) | Runs 3 and 4 passed every step (about 13 min, $3). Run 1 found that the plan never went live, which is fixed | Gate 107 |

The failed and withdrawn ideas are kept with their evidence ([`BRAIN.md`](BRAIN.md) §6). Every finding that changes Hive is mapped to the code that acts on it in [`docs/research_to_product.md`](docs/research_to_product.md). The assistant's whole interaction design is in [`docs/jarvis.md`](docs/jarvis.md).

## How the research works

Every gate pushes its predictions and kill conditions to GitHub **before** it runs (`lab/run_gate.py` refuses to start otherwise), then scores them in its `RESULTS.md`, failures included. Hidden test suites and private intent stay out of the repository until scored. Lab flaws found later are written up, not hidden.

## Repository layout

| Path | Contents |
| --- | --- |
| [`BRAIN.md`](BRAIN.md) | Shared memory: findings and how sure we are, measured constants, evidence log, prediction scorecard, open questions |
| [`hive/`](hive/) | The product. `assistant.py` is the phone assistant; `start.py` the build; `swarm.py` and `guard.py` the builders; `plan.py` business goals; `ship.py` and `deploy.py` pull requests and hosting; `brief.py`, `numbers.py`, `budget.py`, `brain.py`, `safety.py`, `register.py`, `screens.py` and `refs.py` cover the rest |
| [`tests/`](tests/) | About 440 checks with stand-in builders, a fake Telegram and a stand-in model, no network or tokens. They run on every push |
| [`gates/`](gates/) | Every experiment (Gates 0-107): predictions, results, referee code, transcripts |
| [`lab/`](lab/) | Run a gate in one command; [`lab/QUEUE.md`](lab/QUEUE.md) is the queue and session handoff |
| [`docs/`](docs/) | The interaction design ([`jarvis.md`](docs/jarvis.md)), channels ([`channels.md`](docs/channels.md)), the gap plan, the founder session, related work |

## Privacy

Several gates use a real company's code and rules (Company X). Its name, code, rules, documents and the founder's answers are not in this repository; those gates publish aggregate numbers only. Hive keeps an owner's Telegram link, rulings, business notes, numbers, budget and hosting settings in `~/.hive/` on their own machine, never in a repository. Voice notes are transcribed on that machine.

## License

MIT. See [`LICENSE`](LICENSE).
