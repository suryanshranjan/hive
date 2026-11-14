# Hive

**Run your product from your phone. Tell Hive what you want for the business; it works out what to change, builds it with a team of AI coding agents, shows you, and hands it to your engineer. Nothing breaks what already works, and nothing goes live without review.**

Hive is a founder's assistant, in the manner of J.A.R.V.I.S. You talk to it on Telegram in plain words, Hindi-English, voice notes or pictures:
- **Business goals:** "I want more creators signing up this month." Hive reads your product, finds what holds your customers back, and comes back with a short plan in your words. On your yes it builds each step and sends you screenshots.
- **Particular tasks:** "add an invite page".
- **Technical instructions,** if you're technical yourself: "cache /products in Redis, 60 s TTL". It answers in your terms.
- **Pictures:** "make it like this".
- **Complaints:** "a customer says…"
- **Your numbers:** "how many orders came in this week?" Answered from your own data, read-only, once you've connected it.
- **Stepping away:** "I'm sleepy." Hive offers to carry the work on in the cloud so you can shut your computer, or another way.

Getting started is one conversation: say "set me up", and Hive asks whether you run a business, have a product you build, or want to start something new, then gets to know it in about two minutes. Hive asks you only what only you can decide. It builds on copies of your code, checks every test, and arrives as a pull request for your engineer. When it's merged, "put it live" puts it live, and "undo that" takes anything back.

Hive is a research project as much as a product: **108 pre-registered experiments** (*gates*), each scored against predictions pushed before it ran, failures included. Start with [`BRAIN.md`](BRAIN.md) for what is known and how sure we are.

---

## Quick start

One line installs everything Hive needs (git, Python, Node.js, Claude Code, Hive), on a machine with none of it:

```
curl -fsSL https://raw.githubusercontent.com/suryanshranjan/hive/main/install.sh | sh     # Linux, macOS
irm https://raw.githubusercontent.com/suryanshranjan/hive/main/install.ps1 | iex         # Windows (PowerShell)
```

Then, once on the computer (about three minutes), and everything after that is on your phone:

```
claude                                       # log in to Claude once, then /exit
hive setup                                   # your phone (Telegram), screenshots, numbers, where it lives; then live
hive up --repo https://github.com/you/your-product   # or: fetch your code, and Hive is live on your phone
```

Already have Python 3.10+, git and Claude Code? `pip install git+https://github.com/suryanshranjan/hive` is enough.

`hive setup` connects Telegram in two minutes. It offers screenshots, your business numbers and your hosting service, then starts listening and says hello on your phone. Say **"set me up"** there, and Hive gets to know your business or product. After that, everything happens in Telegram. In a terminal, `hive` alone starts one conversation from an idea to a tested branch.

**Optional extras:**

```
pip install playwright && playwright install chromium   # screenshots of what was built, on your phone
pip install "hive-swarm[voice] @ git+https://github.com/suryanshranjan/hive"   # answer by voice note (Whisper, on your machine)
pip install "hive-swarm[data] @ git+https://github.com/suryanshranjan/hive"    # read Postgres, MySQL, Excel and PDF data
npm i -g @openai/codex && codex login       # Codex builders too: "use 2 Claude and 2 Codex"
hive deploy setup vercel                     # where it lives: vercel, netlify, railway, azure, fly, render, or custom
hive numbers setup --url https://.../stats.json   # your numbers, so Hive can tell you whether a change worked
hive brain add docs/                         # your policies, FAQs and notes, so Hive knows the business
hive access add --db postgres://reader:...@host/db   # your data, read-only, so Hive can answer "how many orders this week?"
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

And from Gate 108's company, a made-up lunchbox business whose database Hive was given in setup (replies as sent, after answers were made shorter on the owner's request):

> **You:** How are our cooks paid?
>
> **Hive:** 🐝 Sir, cooks get ₹70 for each lunch they make, paid every Monday for the week before. Your payout records also show something no page mentions: cooks with no complaints in a month get an extra ₹500 on the first Monday of the next month. Is that your rule? I can add it to the cook page.
>
> **You:** How much did we pay our cooks in October, bonuses included?
>
> **Hive:** 📊 We paid our 12 cooks Rs 171,820 in October, bonuses included.

**What you can say:**

| You say | Hive |
| --- | --- |
| *"I want more sign-ups"*, *"sales are low"* | Reads your product and plans 2-4 changes in your words, each grounded in what it saw. It first asks the one thing the product can't show. On your yes it builds them step by step, showing each |
| *"build: an invite page"*, *"add a refund page"* | Says it back in one short line, with the price ("about $0.80"), then builds on your yes |
| *"cache /products in Redis, 60 s TTL"* | A technical instruction is taken as it is: "👍 Yes, let's do it", restated precisely, with at most two normal engineer's questions. From then on it speaks your language |
| A picture + *"make it like this"* | Changes the latest build to match, then sends before and after. In testing a picture matched 18 of 18 times, words 13 of 18 |
| *"set me up"* (offered on your first hello) | Gets to know you in one conversation, about two minutes, every step skippable, picked up where you stopped. First: are you a business, a developer with a product, or starting something new? A business: what it is, your site, your data, how you run things, your host. A developer: the product, where it runs, its data, how it's built and what never to touch, the host. Something new: your idea and what it must do on day one, then the build |
| *"show me"* | Screenshots at phone size of the pages that changed, with a line to ask for tablet or desktop |
| *"show me the pricing page on desktop"*, *"and on tablet?"*, *"on every screen"* | That page on that screen; right after a screenshot, a short "and on tablet?" shows the same pages there |
| *"here's our admin API https://... key: ..."*, a database address, a spreadsheet link | Connected read-only and tried at once ("I can see 12 tables: orders, users, payouts…"). Only one reading query at a time ever runs, in a read-only session; keys stay on your computer |
| *"how many orders came in this week?"*, *"who are my top 5 sellers?"* | Answered from your own data, in plain words. Plans for your goals also read what your data holds |
| *"send me a link"* | The build at its own address, to try on your phone; your live product is untouched. On Vercel the link is private to your Vercel team, and if your product isn't on Vercel yet, Hive asks before its first version goes live. With no host set up, it offers a test copy on your own AWS machine at a private link for two hours, then takes it down (*"take it down"* ends it sooner) and deletes a machine made just for it |
| *"ship it"* | A pull request for your engineer: screenshots, what changed, your words, the test results, the cost |
| *"put it live"* | Only once your engineer has merged it; every test runs on your main version first |
| *"undo that"* | Whatever is most recent, after your yes: a build running stops; an unsent one is set aside; a pull request is withdrawn; live goes back to the version before |
| *"a customer says the sign-up button doesn't work"* | Reads the code and tries the case. Either it's one of your rules at work (change it in a message), or a fault, fixed in one tap |
| *"what's new?"* (and every morning, unprompted) | The brief: what needs you, how your numbers moved since what Hive did, what landed, what customers hit, what it cost |
| *"we had 120 sign-ups this week"* | Kept as a reading, beside what Hive did, so the brief can say "up 18% since the shorter form went to your engineer" |
| A document (policy, FAQ, deck as PDF) | Read; the lasting facts are kept for every plan and answer, and rules it plainly states become your rules |
| *"we're on Vercel"* | Remembered: previews and going live use it (Vercel, Netlify, Railway, Azure, Fly, Render, or your own commands). For Vercel, Hive installs its tool and sends you the sign-in link itself, so nobody needs to be at the computer |
| *"keep running when my laptop is off"*, *"move to the cloud"* | Your choice, at real monthly prices: this computer (free), always on small (about $23 a month), or bigger (about $72), on your AWS account. *"Delete the cloud machine"* stops it. Setup asks the same question |
| *"connect my email"* | Any mailbox: Gmail, Zoho, GoDaddy, Hostinger, Outlook, or your own. It asks for an app password and deletes your message with it from the chat |
| *"any important emails?"*, *"what did Asha say?"* | Read from your mailbox, the ones that matter first. Reading never marks anything read |
| *"reply to Asha saying Thursday works"* | A draft in your voice, with only what you said; sent from your address, in her thread, only when you tap Send |
| *"connect my calendar"*, *"am I free tomorrow at 3?"* | Your Google Calendar's private iCal address; read-only. Today's events open the morning brief |
| *"connect Stripe"*, *"connect Razorpay"*, *"how much did we make this week?"* | Your takings, summed exactly, failed payments flagged. Stripe by a read-only key; Razorpay keys can't be limited, so Hive only ever reads. It never moves money |
| *"I'm sleepy"*, *"good night"*, *"shutting my laptop"* | Says where things stand and offers how to carry on. With work running: moving to the cloud (recommended), so you can shut your computer while it restarts the work there; keeping this computer on; or stopping for tonight. With nothing running: something built overnight, ready with your morning brief |
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
| `hive access [add --db/--url/--file/--cmd \| remove <name> \| ask "..."]` | What Hive may read of your data, read-only; a command source can only be added here, never from the phone |
| `hive rules` (`hive rules forget 3`) | Your standing rulings for this project |
| `hive name "Sunny Shop"` | What Hive calls your project |
| `hive pace fast` / `cheap` | Speed against cost (about 2-3× sooner for about 2× the cost) |
| `hive cloud --new` / `--stop` | A machine on your AWS account, and Hive moved there; deleted when done |
| `hive doctor` | Check that everything is ready |

The lower-level commands for scripts and experiments (`init`, `run`, `owner`, `review`) and the builders' own (`claim`, `land`, `ask`, `assume`) are in `hive --help`.

## How it works

- **It gets to know you first.** "Set me up" asks who you are and follows that path: a business (what it is, your site, your data, how you run things, your host), a developer with a product (how it's built and what never to touch), or something new (the idea and day one, then the build). Every step is skippable, checked as you give it, and kept if you stop.
- **It reads your business, read-only.** Your site, an admin or analytics address with its key, your database (SQLite, Postgres, MySQL), a spreadsheet. Only one checked SELECT at a time runs, in a read-only session, at most 200 rows. Keys stay on your computer. Questions about your figures are answered from it, plans see what it holds, and anything only the data shows (a payment no document mentions) is explained from the data before you're asked.
- **Your business first.** A business goal goes to a planner that reads your product in a throwaway copy. It splits the goal into the questions that decide it, and proposes only steps grounded in something it saw, so a step that cites nothing is dropped. It asks the one thing the product can't show ("do you already give new creators anything?"). Steps are built one after another on one branch, each shown to you.
- **It asks only what only you can decide.** Business edge cases come as concrete situations ("a refund half paid by points: back to the card, or as points?"), and plain facts as plain questions. Your answers become rules, encoded as tests. Questions never invent facts about your business. On your phone they come one at a time: the next only once you have answered the last.
- **Your work adds up.** A new request builds on top of your latest unmerged build, so everything reaches your engineer as one pull request (Gate 107).
- **A safety net when there are no tests.** Most founders' projects have few tests. Hive first writes tests that pin how the product behaves today, then builds, so "every test passes" means something.
- **A look is shown, not quizzed.** A change to how a page looks gets one builder, no questions, and screenshots as the review. It can take the look of a site you name (never its logo, name or words).
- **The swarm law sets the team.** How many builders, from your tests' speed, your machine and the job's parts. Choose differently and it tells you once what the law would pick.
- **Builders never talk; a guard keeps the peace.** Each claims an area with a lock file, works in its own clone, and lands through the guard. The guard refuses anything that breaks a passing test, duplicates a definition or commits a secret. Claude, Codex and Gemini builders mix in one team (Gate 47).
- **Checked before every delivery.** The goal's stated interfaces (Gate 84), your own examples run through the product's functions (Gate 103), and every test.
- **It remembers.** Your rulings, your business notes and your documents carry into every later build and answer. Contradictions with an earlier ruling are put to you.
- **Expired logins don't stop the work.** If your AWS or GitHub sign-in has expired when Hive needs it, it sends you the sign-in link on your phone, takes the code it shows you, and carries on. It never switches to a different account without asking.
- **It notices when you step away.** "I'm sleepy" gets where things stand and a choice. With work running, it recommends the cloud: the work is handed over and restarted there before anything stops here, so you can shut your computer. Or keep this computer on, or stop for tonight. With nothing running, it offers to build something overnight.
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
| Run a company's numbers through Hive | After fixes, run 3: onboarding in 0.3 min, 10 of 10 figure answers from the data, a ₹500 rule found only in the payouts and explained, screens on every device, a 3-step plan built (7.9 min, $0.76). Runs 1-2 found 2 faults (a build that couldn't start; queries dropped, which fired the kill at 5 of 10), both fixed. Run 4 repeated run 3, and its plan found all 4 planted problems | Gate 108 |
| Run the office from the phone: mail, calendar, payments | On a real mail server, Stripe's official mock and the real model: the mails that matter in 50 words, nothing marked read, a reply sent in-thread only on your tap, the week's takings exact with a failed payment flagged, "am I free?" answered. Stand-ins, not real accounts yet | Gate 112 |
| Always on, your choice | On real AWS: offered at real monthly prices; the size you pick is made; Hive listens there; "delete the cloud machine" deletes it (2.3 min, $0.002) | Gate 111 |
| Run hosting from the phone, on real Vercel | Hive installed Vercel's tool itself and connected; a link to try; "put it live" refused before the merge, done on your yes; "undo that" took it back; everything deleted, nothing else touched, $0. It first found Vercel puts a new project's first version live (now Hive asks) | Gate 110 |
| Hand the work to the cloud and back, on real AWS | "I'm sleepy" with a build running: moved to a t3.small in 2.4 min; the work restarted there, his 2 answers asked on Telegram and built in (10 tests passing); the work came home and the machine was deleted, nothing left billing (29 min, $0.88). The test page first failed on a bug, then, fixed, went up at a private link and came down (3.4 min) | Gate 109 |

The failed and withdrawn ideas are kept with their evidence ([`BRAIN.md`](BRAIN.md) §6). Every finding that changes Hive is mapped to the code that acts on it in [`docs/research_to_product.md`](docs/research_to_product.md). The assistant's whole interaction design is in [`docs/jarvis.md`](docs/jarvis.md).

## How the research works

Every gate pushes its predictions and kill conditions to GitHub **before** it runs (`lab/run_gate.py` refuses to start otherwise), then scores them in its `RESULTS.md`, failures included. Hidden test suites and private intent stay out of the repository until scored. Lab flaws found later are written up, not hidden.

## Repository layout

| Path | Contents |
| --- | --- |
| [`BRAIN.md`](BRAIN.md) | Shared memory: findings and how sure we are, measured constants, evidence log, prediction scorecard, open questions |
| [`hive/`](hive/) | The product. `assistant.py` is the phone assistant; `start.py` the build; `swarm.py` and `guard.py` the builders; `plan.py` business goals; `onboard.py` setting up; `access.py` reading your data, read-only; `logins.py` renewing sign-ins; `trydeploy.py` test deploys; `ship.py` and `deploy.py` pull requests and hosting; `brief.py`, `numbers.py`, `budget.py`, `brain.py`, `safety.py`, `register.py`, `screens.py` and `refs.py` cover the rest |
| [`tests/`](tests/) | About 530 checks with stand-in builders, a fake Telegram and a stand-in model, no network or tokens. They run on every push |
| [`gates/`](gates/) | Every experiment (Gates 0-108): predictions, results, referee code, transcripts |
| [`lab/`](lab/) | Run a gate in one command; [`lab/QUEUE.md`](lab/QUEUE.md) is the queue and session handoff |
| [`docs/`](docs/) | The interaction design ([`jarvis.md`](docs/jarvis.md)), channels ([`channels.md`](docs/channels.md)), the gap plan, the founder session, related work |

## Privacy

Several gates use a real company's code and rules (Company X). Its name, code, rules, documents and the founder's answers are not in this repository; those gates publish aggregate numbers only. Hive keeps an owner's Telegram link, rulings, business notes, numbers, budget, hosting settings and data access (with its keys, readable by the owner only) in `~/.hive/` on their own machine, never in a repository. It only ever reads his data, and asks for read-only logins. Moving Hive to the cloud copies these to his own machine there. Voice notes are transcribed on that machine.

## License

MIT. See [`LICENSE`](LICENSE).
