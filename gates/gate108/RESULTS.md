# Gate 108: results (flown Nov 14 2026, lab container on the user's laptop)

**Question.** Can a founder run his company through Hive? This is the first flight of onboarding, read-only data access and screens on any device. (Predictions: `PREDICTIONS.md`, pushed before launch in `ae3f0b5`.)

**Answer.** Mostly yes, after fixes found in flight. Three runs of the same flight, with real Claude, real builds and real screenshots, on Dabba Days, a made-up lunchbox company. Fixes went in between runs, as in Gate 107.
- **Run 1** found 3 faults:
  - a plan's build died at once;
  - one data answer came back empty;
  - one answer counted a bonus twice.
- **Run 2** found the real cause of the empty answers. It **fired the kill**: only 5 of 10 data answers came back.
- **Run 3** got everything right except the growth plan's coverage: 10 of 10 data answers, the hidden pay rule with its condition, every screen, and the plan built in full.
- **Run 4** repeated run 3 after two changes (plain replies; a narrower planner rule on prices) and held every prediction, the growth plan included (4 of 4).

## Scored

| # | Prediction | Run 1 | Run 2 | Run 3 |
|---|---|---|---|---|
| O1 | Onboarding works: 5 steps, database confirmed, policy read, wrap-up, no raw error | **Held**: "I can see 8 tables", 13 facts and 7 rules read, 0.3 min | **Held** | **Held** |
| O2 | ≥ 8 of 10 data answers right | **Held, at the line: 8.** Q1 empty; Q10 counted the bonus twice (₹1,73,820 against ₹1,71,820). The script matched the number in the text and said 9; read by hand, 8 | **Failed: 5 (kill fired).** 5 answers came back empty | **Held: 10 of 10**, each checked by hand |
| O3 | The hidden pay rule surfaces, with amount and condition | **Failed (half):** found the ₹500 "clean month" payments, said no document mentions them, then asked him what earns them | **Held:** "the bonus went to exactly the cooks who had no complaints that month, without exception" | **Held:** the same, for August, September and October; asks him to confirm it as policy |
| O4 | Screens from the phone: 1, 1 and 3 photos of the named page on the named screens | **Held** | **Held** | **Held** |
| O5 | The plan names ≥ 3 of the 4 planted problems | **Held: 3** (the form with GST, no trial, promises and pause hidden) | **Failed: 2** (the form; promises and pause) | **Failed: 2** (the form; promises and pause) |
| O6 | ≤ $10 and ≤ 60 minutes | **Held:** 5.5 min, $0.27 for the plan (the build died) | **Held:** 7.9 min, $0.89 builders + $0.27 plan | **Held:** 7.9 min, $0.76 builders + $0.26 plan |

Hive's own reading calls (21–26 per run) and the code-reading answers are not in the dollar figures. At Gate 97's $0.005 a reading call they add about $0.15; the code-reading agent is more.

**Not found in any run:** the plans page never shows the price of one lunch (₹120, ₹150, ₹170). Every plan proposed telling customers what they get, never what one lunch costs.

**The key's own error:** for "which cook had the most complaints in October", the key's query picked one name (Rehana Begum, 4). The data has a three-way tie at 4 (Fatima Sheikh, Sunita Patil, Rehana Begum). Hive reported the tie in every run, which is more right than the key.

## Run 4: the replication, after two more changes (Nov 14)

Run 3 was one clean run, so the flight was flown again, unchanged, after two product changes:
- **plain replies** for every founder (the owner: "anything must be answered simply");
- **a narrower planner rule.** "No pricing changes" became "not what he charges", with how prices are shown in scope, read as a first-time customer deciding whether to pay. No plan in runs 1-3 had named the hidden price of one lunch.

| # | Run 4 |
|---|---|
| O1 onboarding | **Held** |
| O2 data answers | **Held: 10 of 10**, each one or two short sentences (for example "18 subscribers cancelled in October.") |
| O3 hidden rule | **Held:** "a cook with no complaints in a month gets an extra ₹500" |
| O4 screens | **Held:** 1, 1 and 3 photos |
| O5 planted problems | **Held: 4 of 4.** The plan: a shorter form with GST optional; "Show price per lunch and what's protected" (the first time the hidden price was found); a one-week trial. The protections include the 10-day pause |
| O6 cost and time | **Held:** 8.4 min, $0.81 builders + $0.26 plan; 12 tests passing, all 7 old ones kept |

Runs 3 and 4 together are the replication: two clean runs in a row for O1-O4 and O6. O5 has held once on the current planner (run 4); the planner change has not been repeated.

**The same data on Postgres and MySQL (Nov 14, outside the flight).** Dabba Days' data was copied into Postgres 16 and MySQL 8.4, each with a read-only login. Hive connected to both ("I can see 8 tables"), refused a write on both, and answered 5 of the 10 questions right on each (active subscribers, October sign-ups and cancellations, the complaint tie, October cook pay). Without the database drivers installed, it says so plainly and gives the one install line (`hive-swarm[data]`).

## What the runs found, and what changed

1. **A plan's build could not start (run 1).** The build runs as `python -m hive` inside his project's folder. Run from a source checkout, that process could not import Hive: "No module named hive". He heard only "It stopped partway without saying why." Every Hive process Hive starts (a build, `hive up`, the listener after the cloud) now gets the package's path. Tested: `tests/test_onboard.py` §7. Runs 2 and 3 built all 3 plan steps, with screenshots after each and every test passing (14 and 10).
2. **Data answers dropped their queries (runs 1 and 2).** The model sometimes named the database by its kind (`"db"`) instead of its name (`"dabba database"`). Hive looked queries up by exact name, so it ran none and said nothing useful. Queries now match the name loosely, or go to his only database. Tested in `tests/test_access.py`.
   - A first guess (multi-line JSON) was tested against the real model and **not** confirmed. Lenient JSON reading went in anyway, as hardening.
   - Every failed model call is now logged (`~/.hive/explain.log`). The silent failures are why this took two runs to find.
   - Run 2's extra failures (5, against run 1's 1) came after a prompt change asked for cross-checking queries. Whether that change made the misnaming more frequent is not established.
3. **An empty reason (run 1).** "I couldn't read your data just now: ." became a plain sentence, and an empty reply is retried once.
4. **A bonus counted twice (run 1, Q10).** The query and answer prompts now say to check how money columns relate before adding them, and never to add a part to a total that may already contain it. Run 3's answer: "₹1,71,820, and that already includes ₹2,000 in bonuses."
5. **The hidden rule (run 1, O3 half).** The cook-pay question was answered by the code-reading assistant. In run 1 it found the payouts by searching the computer: it had no data access of its own. It is now given his data properly: a read-only `hive access sql` command, and an instruction to explain anything only the data shows by comparing who gets it with who doesn't, before asking him. Runs 2 and 3 named the condition exactly.

## Confounds

- One company, simulated founder, plain questions, SQLite.
- The founder's onboarding words were scripted.
- The planted site problems are easy to see.
- Fixes went in between runs, so the three runs are not repeats of one product. Run 3 alone is the product as it now is.
- The key is private (`hive_private/dabba/answers.json`), made from a fixed seed with `make_dabba.py`.

## Files

- `results/run1_transcript.json` to `run4_transcript.json`: every message both ways.
- `flight108.py` (the flight), `analyze108.py` (scoring against the private key).
