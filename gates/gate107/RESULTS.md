# Gate 107: results (flown Nov 3 2026, lab container on the user's laptop)

**Question.** Does the whole product hold together for a fresh founder, end to end, on his phone? (Predictions: `PREDICTIONS.md`, pushed before launch in `857d06b`.)

**Answer.** Yes, after two fixes. Four runs of the same 14 steps, with real Claude, real builds and real screenshots, on a creator site with no tests:
- **Run 1** exposed a serious fault: the plan's work never went live.
- **Run 2** exposed the bug inside that fix.
- **Runs 3 and 4** passed every step, about 13 minutes and $3 a run.

Each run also found smaller things, all fixed.

## The runs

| Run | Steps right (of 13 Hive steps) | What it showed | Fixed in |
|---|---|---|---|
| 1 | 13 by the letter, but the product was wrong | **Serious:** the technical build started from his main, not from the plan he hadn't shipped yet. "Ship it" sent only the email check, and **the plan's changes never reached his live product** (the complaint then found the old 9-field form). Also: "your new ruling" and a branch name after a picture change and a complaint fix; captions read "/"; "Put it live on Custom?"; the change's name not quoted | `7ce9f91`: a build from the phone goes on top of his latest unmerged build, which is then folded in (its pull request withdrawn); Hive's own words after a change; "Home page"; "your site"; quotes |
| 2 | 9 | The fix's own bug: building on top of a branch left Hive's copy with no "main", so the step-6 builders had nowhere to work. Preview, ship and live then had no build. Also: a delete of an already-gone folder crashed the build | `325c76f`: Hive's copy names the earlier build as his branch (`tests/test_start.sh` checks a build on top keeps the earlier work); the delete tolerates a missing folder |
| 3 | **13** | The plan's work was live after "put it live" (the old home page gone). Also: each plan step's screenshots showed only the home page; the brief said "Good morning" at his 5 pm (the lab's clock is UTC) | `48be326`: screenshots of the pages the work changed; his clock, kept at setup |
| 4 | **13** | The flight now carries a background build's news, as `hive listen` does; runs 1-3 never saw the after-build report. Report reached: "Sir, it's done. The sign-up form now checks the email before it sends...", with the sign-up page. Screenshots of the changed pages: sign-up, invite, dashboard. The plan's work is inside what went live (checked by git ancestry). Still: the brief's own words said "Good morning" at his 5:40 pm | Fixed after the run: the brief is told his time and greeting (not yet flown) |

**Run 3 and 4 in numbers:**
- **Run 3:** 12.7 minutes, $3.20 for the builders, plan $0.21.
- **Run 4:** 13.9 minutes, $2.62, plan about $0.21.
- **The safety net** wrote 94 (run 1), 25 (run 3) and 21 (run 4) tests on a project that had none; every later delivery reported them passing.

**What the founder saw (run 4, abridged):**
- **The question about what the product can't show:** "Is the ₹500 first-deal bonus open to every new creator...?"
- **The plan:** 3 steps in plain words, with one owner-only question: "Do creators need a GST number to get paid?"
- **Each step shown:** "✅ Step 2 of 3 done: A home page that talks to creators", with the home and sign-up pages.
- **The technical instruction:** "👍 Yes, let's do it", restated precisely, then the after-build report.
- **Shipping and live:** a preview link; "Put it live on your site?"; "It's live"; then "Put your live product back to how it was before "..." went live?" and "Done".
- **The complaint:** traced to the form demanding GST and address, then "✅ Fixed, sir".
- **The brief and the budget:** a brief naming what needs him first; the budget confirmed with this month's spend.

## Predictions scored

| # | Prediction | Result |
|---|---|---|
| E1 | >= 12 of 13 steps right first time | **Held in runs 3 and 4** (13, 13). **Failed in run 2** (9). Run 1 was 13 by the letter, but its live product lacked the plan's work. |
| E2 | Nothing raw reaches him | **Held, all runs:** no traceback, raw error or "went wrong on my side". Run 2's crashed build sent him nothing at all, a silence the flight caused (see run 4). |
| E3 | He never needs his computer | **Held:** no command or file asked of him. "Your engineer should undo the merge" and "Uploaded as branch ..." are addressed to his engineer. |
| E4 | The safety net works | **Held:** 94 / 25 / 21 tests, passing, reported in every delivery |
| E5 | <= $15 and <= 90 min | **Held:** about $3 and 13-14 minutes a run |

## What it changes

- **Building on top of his latest unmerged build:** a build from the phone always does this now, so his work adds up in one line and one pull request.
- **Plain words after every change.**
- **Screenshots of the pages a change touched.**
- **His clock** for the brief.

Hive is ready for a second founder on a practice project. A real product is the next test.

**Confounds:**
- One run per fix.
- A simulated founder and a stand-in host and engineer.
- A mock project with plain-to-see problems.
- Run 4's live check by headline text was a weak proxy: the builder kept the old headline and added a section beneath it. Git ancestry showed the plan's work was inside what went live.

**Files:** `results/run1_transcript.json` to `run3_transcript.json` and `transcript.json` (run 4): every message both ways, each step's outcome, minutes and cost.
