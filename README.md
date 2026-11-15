# Hive

**Run your company from your phone.** Tell Hive what you want for the business, in plain words. It works out what to change, builds it with a team of AI coding agents, shows you screenshots, and hands it to your engineer. It also reads your mail, calendar, payments and data, and answers you on Telegram.

Hive is also a research lab. Every feature in it came out of one of **113 pre-registered experiments**, each scored against predictions published before it ran, failures included. [Why that matters](#why-hive-is-research-not-a-demo).

---

## What Hive does

Hive is a founder's assistant in the manner of J.A.R.V.I.S., and a shipping tool for developers ([below](#if-youre-a-developer-who-just-wants-to-ship)). You talk to it on Telegram: text, Hindi-English, voice notes or pictures.

| You want to… | You say | Hive |
| --- | --- | --- |
| Grow the business | *"I want more creators signing up this month"* | Reads your product, finds what holds customers back, and proposes a short plan with a price. On your yes it builds each step and sends screenshots |
| Get something built | *"add an invite page"*, *"make it like this"* + a picture | Says it back in one line with the price, builds it, shows you |
| Know your numbers | *"how many orders came in this week?"* | Answers from your own data, read-only |
| Handle your office | *"any important emails?"*, *"reply to Asha saying Thursday works"*, *"am I free at 3?"*, *"how much did we make this week?"* | Reads your mailbox, Google Calendar, Stripe or Razorpay. A reply goes out only when you tap Send. It never moves money |
| Ship it | *"ship it"*, *"put it live"*, *"undo that"* | A pull request for your engineer; live only after it's merged and every test passes; anything taken back |
| Step away | *"I'm sleepy"* | Offers to carry the work on in the cloud so you can shut your laptop |

It asks you only what only you can decide, one question at a time.

### If you're a developer who just wants to ship

Hive works the same way for you, in your terms:

- **Say it technically, and it's taken as is.** *"cache /products in Redis, 60 s TTL"* gets "👍 Yes, let's do it", your instruction restated precisely, and at most two questions a normal engineer would ask. No business talk.
- **Hand it your backlog and go.** `hive start --overnight` builds while you sleep; the builders write their questions down, and you answer them over breakfast (`hive morning`).
- **Every change arrives as a pull request** with the diff, the test results, screenshots and the cost. Nothing touches `main`, nothing goes live until you merge, and every existing test must keep passing.
- **Bring your own agents.** Claude, Codex and Gemini builders mix in one team (*"use 2 Claude and 2 Codex"*); a guard refuses anything that breaks a passing test, duplicates a definition or commits a secret.
- **From the terminal too.** `hive` alone runs one conversation from an idea to a tested branch, no phone needed.
- **Honest about cost.** On real Django issues one builder solved 8 of 10, and a full swarm also 8 of 10 at 15 times the cost (Gates 86, 89). So on a technical task Hive uses one builder, and saves the swarm for big jobs with many independent parts.

### Rules it never breaks

- It never changes your main code directly, never skips the tests, and never puts anything live that your engineer hasn't merged.
- It only **reads** your data, mail, calendar and payments. It never sends a mail without your tap and never moves money.
- Your keys and passwords stay on your own machine. A chat message carrying a password is deleted after use.

---

## Quick start

**1. Install** (one line; installs git, Python, Node.js, Claude Code and Hive if they're missing):

```
curl -fsSL https://raw.githubusercontent.com/suryanshranjan/hive/main/install.sh | sh     # Linux, macOS
irm https://raw.githubusercontent.com/suryanshranjan/hive/main/install.ps1 | iex         # Windows (PowerShell)
```

**2. Two commands on the computer** (about three minutes):

```
claude          # log in to Claude once, then /exit
hive setup      # connects your phone (Telegram); then Hive says hello there
```

**3. On your phone, say "set me up".** Hive asks whether you run a business, build a product, or are starting something new, and gets to know it in about two minutes. Everything after that happens in Telegram.

### What it costs

- **Claude:** Hive's builders run on Claude Code, so you need a Claude subscription (Pro or Max) or an Anthropic API account. That is the only thing you must pay for.
- **Each job:** Hive tells you the price before it starts, and asks before going past your budget (*"set my budget to $50 a month"*). In the tests, a small change cost about $0.80, a three-step plan about $1.50 to $3, and answering from your data a few cents.
- **Always on (optional):** a machine on your own AWS account, about $23 a month (small) or $72 (bigger). Or keep it on your computer for free.
- **Hosting, mail, calendar, payments:** Hive uses the accounts you already have; it adds no fee of its own.

Already have Python 3.10+, git and Claude Code? `pip install git+https://github.com/suryanshranjan/hive` is enough.

<details>
<summary><b>Optional extras</b></summary>

```
pip install playwright && playwright install chromium   # screenshots on your phone
pip install "hive-swarm[voice] @ git+https://github.com/suryanshranjan/hive"   # voice notes (Whisper, on your machine)
pip install "hive-swarm[data] @ git+https://github.com/suryanshranjan/hive"    # Postgres, MySQL, Excel and PDF data
npm i -g @openai/codex && codex login       # Codex builders too: "use 2 Claude and 2 Codex"
hive deploy setup vercel                     # your host: vercel, netlify, railway, azure, fly, render, or custom
hive access add --db postgres://reader:...@host/db   # your data, read-only
hive brain add docs/                         # your policies and FAQs, so Hive knows the business
hive cloud --new                             # always on: a machine on your AWS account
```

Most of these can also be done from the phone ("connect my email", "we're on Vercel", "move to the cloud").
</details>

---

## What it's like

A real exchange from an end-to-end test (Gate 107), shortened:

> **You:** I want more creators signing up this month.
>
> **Hive:** ❓ Before I plan it, one thing your product can't tell me: is the ₹500 first-deal bonus open to every new creator?
>
> **Hive:** 🧭 Here's what I see. A creator can only reach sign-up from a small footer link, then faces 9 required fields, bank details included, before seeing any deal. What I'd do:
> 1. **A shorter sign-up form**
> 2. **A home page that talks to creators**
> 3. **Make the invite reward easy to see**
>
> All of it: about $1.50. **[🚀 Yes, do it all] [Just the first] [Not now]**
>
> **Hive:** ✅ Step 1 of 3 done. *(screenshot)* … 🎉 That's the plan done. 22 tests, all passing. Say *ship it*.
>
> **You:** ship it → ✅ Sent to your engineer.
>
> **You:** put it live → ✅ It's live.

And on a mock lunchbox company whose database Hive was given:

> **You:** How are our cooks paid?
>
> **Hive:** 🐝 Cooks get ₹70 for each lunch, paid every Monday. Your payout records also show something no page mentions: cooks with no complaints in a month get an extra ₹500. Is that your rule?

That ₹500 rule was hidden in the data on purpose. Nobody told Hive about it.

---

## Why Hive is research, not a demo

Most AI agent products show a demo that worked. Hive publishes **every experiment, including the ones that failed**, and builds only what the evidence supports.

### How each experiment (a *gate*) runs

1. **Predictions first.** Before a run, the exact predictions and a *kill condition* (the result that would prove the idea wrong) are pushed to GitHub. The lab script refuses to start otherwise (`lab/run_gate.py`).
2. **Hidden tests.** Builders are scored on test suites they never see, so they can't game them. Hidden suites stay out of the repo until the run is scored.
3. **Controlled comparisons.** Many gates run two arms that differ in one thing (with and without owner questions, a picture against words), in randomized order, often with a blind judge.
4. **Every result is written up** in `gates/gate<k>/RESULTS.md`. When a kill condition fires, that is recorded and the idea is dropped or changed. Kills fired in Gates 27, 29, 31 and 35-38, among others.
5. **Every finding changes the product, or says why not.** [`docs/research_to_product.md`](docs/research_to_product.md) maps each result to the code that acts on it.
6. **One shared brain.** [`BRAIN.md`](BRAIN.md) holds what is known and how sure we are (*established*, *model* or *conjecture*), the measured constants, a scorecard of every prediction, and the open questions.

### What the research found

These shaped Hive's design, and several went against what we expected.

- **AI coding agents can build together without talking.** Swarms of up to 12 agents, coordinating only through git, finished projects of up to 1,340 tests, never gamed the tests, and rarely collided (Gates 1-3, 10). Giving them a message board added nothing (Gates 43, 44). *So Hive's builders work silently, behind a guard.*
- **The limit isn't code, it's knowing what the owner wants.** On rules a model can't guess, swarms passed every visible example but only 35-58% of hidden tests (Gates 3-17).
- **Examples the owner picks beat questions the agents ask.** Owner-chosen examples fixed 2.7 times as many errors as builder-chosen ones (Gate 13). On a real company's rules: 84.8% against 49.6% (Gates 18, 20).
- **A real founder can't reliably state their own rules, but can correct a description of what was built.** The founder's answers to two framings of the same decision agreed 1 time in 8, and rules the founder confirmed didn't hold a day later (Gates 36-38). A plain sheet of what the code does, corrected by the owner, reached 99.6-100% (Gates 42, 44). *So Hive shows you what it built and asks about concrete situations, not abstract rules.*
- **One agent that asks beat a team working from a hand-over,** by 21-30 points (Gates 66, 68). *So Hive's builders ask first.*
- **A picture beats words for how something should look:** 18 of 18 checks against 13 of 18 (Gate 105). *So Hive takes "make it like this" with a picture.*
- **Give it the business goal, not the task.** From "more sign-ups" alone, Hive found and built 8 of 9 planted problems, with 4 owner messages (Gate 106). It repeated this on a second mock company in another trade (Gate 113).
- **A law for team size.** How many builders to use comes from a fitted formula (coupling between agents, the test gate's speed, and how fast the owner's intent arrives), measured on real runs ([`BRAIN.md`](BRAIN.md) §3).

### What is still unproven

- Most recent gates use a **simulated founder** answering from a written policy, on mock companies made by the same author.
- Many results come from **one run per arm**.
- The real test, **a founder using Hive on their own company**, hasn't happened yet. The office (mail, calendar, payments) has run on real protocols with test servers, not on real accounts.

---

## The evidence, gate by gate

Every result below was predicted on GitHub before the run. Real-company results publish aggregate numbers only.

| Finding | Result | Where |
| --- | --- | --- |
| Silent swarms finish and don't game the tests | Visible and hidden pass rates within 0.4 points | Gates 1-3 |
| Without the owner, swarms miss the rules no one wrote down | 24-58% of hidden tests | Gates 3-24 |
| Owner examples and questions carry intent | 95-98% hidden | Gates 13, 17, 24 |
| On a real company's rules and backend | 84.8% against 49.6%; real features 23/23 and 18/18, every existing test kept | Gates 20, 25, 26 |
| The real founder audits lists poorly but answers situations | Marked 0 of 27 in a list; answered 48 of 48 situations | Gates 35-38 |
| The owner corrects a sheet written from the built code | 99.6% and 100% hidden, against 68.4% from the interview | Gates 42, 44 |
| Claude and Codex builders in one swarm | 1,340/1,340, 100% hidden, no breaks of main | Gate 47 |
| One agent that asks vs Hive's hand-over | The asking agent won by 21-30 points; Hive's builders now ask first | Gates 66, 68 |
| Overnight questions answered in the morning | 94.2% against 75.0% for a morning hand-over | Gate 70 |
| A split swarm (one builder owns the owner's decisions) | One agent's accuracy (90.0 vs 86.5%) in 0.45× the time, at 1.95× the cost | Gates 74, 75 |
| Real Django issues | One builder 8/10; `hive start` 8/10 at 15× the cost. On technical goals Hive now acts like one builder | Gates 86, 89 |
| Reliability and owner load | pass^5 held (10 of 10); owner prompts 55 → 23 per feature | Gates 93-104 |
| Memory against silent drift; the owner's examples checked before delivery | 27-29 of 29 with memory (20, 29, 17 without); the check caught a refund sent the wrong way | Gates 101, 103 |
| A picture vs words for a look | 18/18 against 13/18; a blind judge preferred the picture 3 of 3; same cost | Gate 105 |
| Give it the business, not the task | 8 of 9 planted problems found and built from a goal alone, 4 owner messages | Gate 106 |
| A fresh founder end to end (14 steps on the phone) | Runs 3 and 4 passed every step (about 13 min, $3). Run 1 found the plan never went live; fixed | Gate 107 |
| Run a company's numbers through Hive | Onboarding in 0.3 min, 10 of 10 figure answers, a hidden ₹500 rule found in the payouts, screens on every device, a plan built (7.9 min, $0.76). Earlier runs found 2 faults, both fixed | Gate 108 |
| Hand the work to the cloud and back, on real AWS | "I'm sleepy" mid-build: moved to the cloud in 2.4 min, the work finished there and came home, the machine deleted (29 min, $0.88) | Gate 109 |
| Run hosting from the phone, on real Vercel | Hive installed Vercel's tool and connected itself; a preview link; "put it live" refused before the merge, done on yes; "undo that" worked; everything deleted, $0 | Gate 110 |
| Always on, your choice | On real AWS, at real monthly prices: the size you pick is made, Hive listens there, "delete the cloud machine" deletes it (2.3 min, $0.002) | Gate 111 |
| The office from the phone: mail, calendar, payments | On a real mail server, Stripe's official mock and the real model: important mail in 50 words, nothing marked read, a reply sent in-thread only on your tap, takings exact with a failed payment flagged. Test servers, not real accounts yet | Gate 112 |
| A second company, another trade | FixKaro (mock appliance repair): setup, 9 of 10 figures, a hidden pay rule found, screens on every device, a plan that found 3 of 4 planted problems (8 min, $1.07) | Gate 113 |

The failed and withdrawn ideas are kept with their evidence ([`BRAIN.md`](BRAIN.md) §6). The assistant's interaction design is in [`docs/jarvis.md`](docs/jarvis.md).

---

## How it works

- **It gets to know you first.** "Set me up" follows your path (business, developer, or new idea). Every step can be skipped and is picked up where you stopped.
- **It plans from your business.** A goal goes to a planner that reads your product in a throwaway copy and proposes only steps grounded in something it saw. It asks the one thing the product can't show.
- **It asks only what only you can decide,** as concrete situations ("a refund half paid by points: back to the card, or as points?"). Your answers become tests.
- **A safety net when there are no tests.** It first writes tests that pin how the product behaves today, so "every test passes" means something.
- **Builders never talk; a guard keeps the peace.** Each builder works in its own copy and lands through a guard that refuses anything that breaks a passing test or commits a secret. Claude, Codex and Gemini builders can mix in one team.
- **It reads your business, read-only:** database, spreadsheet, admin API, mailbox, calendar, payments. Only one checked read-only query runs at a time.
- **It remembers** your rulings, business notes and documents, and asks when something contradicts an earlier ruling.
- **It speaks first:** a morning brief at your local time, a builder stuck, a step done, always with the reason.
- **It handles the chores.** Expired AWS, GitHub or Vercel sign-ins come to your phone as a link, and it installs the tools it needs.

## Commands

Everything works from the phone; these are for the computer.

| You type | What happens |
| --- | --- |
| `hive setup` | First run: Telegram, voice, screenshots, numbers, your host; then live on your phone |
| `hive up [--repo <address>]` | Listening on your phone now, in the background; `--repo` fetches your code first |
| `hive` | One conversation in the terminal, from an idea to a tested branch |
| `hive start --overnight` | Builds while you're away; questions wait for your morning |
| `hive morning [--phone]` | Answer the overnight questions; your answers are built in |
| `hive deploy setup <host>` / `preview` / `status` | Your host; a preview of the latest build |
| `hive access [add ... \| remove <name> \| ask "..."]` | What Hive may read of your data, read-only |
| `hive brain add <file or folder>` | Teach Hive your business from documents |
| `hive numbers [setup ... \| add name=value]` | Your business numbers, as they move |
| `hive rules` | Your standing rulings for this project |
| `hive pace fast` / `cheap` | Speed against cost |
| `hive cloud --new` / `--stop` | Always on: a machine on your AWS account; deleted when done |
| `hive doctor` | Check that everything is ready |

Lower-level commands for scripts and experiments are in `hive --help`.

## Repository layout

| Path | Contents |
| --- | --- |
| [`BRAIN.md`](BRAIN.md) | What is known and how sure we are: findings, constants, evidence log, prediction scorecard, open questions |
| [`hive/`](hive/) | The product. `assistant.py` the phone assistant; `start.py` the build; `swarm.py` and `guard.py` the builders; `plan.py` business goals; `onboard.py` setup; `access.py` your data; `office.py` with `mail.py`, `calendar_.py` and `payments.py` the office; `cloud.py` and `cloud_aws.py` always-on; `ship.py`, `deploy.py` and `trydeploy.py` shipping and hosting; `logins.py` sign-ins |
| [`tests/`](tests/) | Hundreds of checks with stand-in builders, a fake Telegram and a stand-in model; no network or tokens. They run on every push |
| [`gates/`](gates/) | Every experiment: predictions, results, referee code, transcripts |
| [`lab/`](lab/) | Run a gate in one command; [`lab/QUEUE.md`](lab/QUEUE.md) is the queue and session handoff |
| [`docs/`](docs/) | Interaction design, channels, the research-to-product map, the founder session plan, related work |

## Privacy

Several gates used a real company's code and rules (Company X). Its name, code, rules and the founder's answers are not in this repository; those gates publish aggregate numbers only. Hive keeps everything about an owner (Telegram link, rulings, notes, numbers, data access, mail, calendar and payment keys) in `~/.hive/` on their own machine, readable only by them, never in a repository. Moving Hive to the cloud copies these to the owner's own cloud machine. Voice notes are transcribed on that machine.

## License

MIT. See [`LICENSE`](LICENSE).
