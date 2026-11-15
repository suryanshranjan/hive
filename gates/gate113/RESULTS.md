# Gate 113: results (Nov 15 2026)

**Question.** Does Gate 108 replicate on a second company in another trade? The company was FixKaro, a made-up appliance-repair service in Pune. It ran as one flight, real Claude, on today's Hive.

**Yes.** Every prediction held: R4 on a re-run after a launch mistake of mine, and R2 at 9 of 10, its one miss since fixed. Most importantly, **the planner's price rule replicated**: the plan's second step was to show what a visit costs, on a company it had never seen.

| # | Prediction | Result |
|---|---|---|
| R1 | Onboarding works | **Held:** all 6 steps, including the new "Where should I run?" (he kept this computer); "I can see 8 tables"; the policy read ("10 things kept"); the wrap-up, 0.3 min |
| R2 | ≥ 8 of 10 data answers right | **Held: 9 of 10.** The miss: October technician pay, ₹47,195 against ₹48,095. Hive took the ₹900 deduction off a total that was already net (below) |
| R3 | The hidden rule surfaces | **Held:** "Your payouts show one thing your policy doesn't: they're paid nothing for a free 7-day re-fix and lose another ₹100 for each one. Is that your rule?" |
| R4 | Screens 1, 1, 3 | **Failed in the flight, held on re-run.** The flight's home had no screenshot browser, because I left out `PLAYWRIGHT_BROWSERS_PATH` at launch, which a clean home needs (`lab/QUEUE.md`). Hive said so plainly: "I can't take screenshots on this machine yet: the browser isn't installed (run: playwright install chromium)." With the browser found (`screens113.py`): 1, 1 and 3 photos |
| R5 | The price rule replicates | **Held:** step 2, "Show what a visit costs, up front. Every service card says only 'Price on inspection', and no page mentions the ₹299 visit fee, that it is waived if FixKaro does the repair…" |
| R6 | ≥ 3 of 4 planted problems | **Held: 3 of 4.** Found: the account forced before booking (11 fields); the hidden price; the service areas never named. Missed: no way to change a slot, only cancel |
| R7 | ≤ $10, ≤ 60 min | **Held:** 8.1 min; $0.83 builders + $0.24 plan |
| Kill | < 6 of 10 | Not fired |

**The planted problems and the hidden rule**, named now that the run is scored:
- **The problems:**
  1. the services page shows no price, only "Price on inspection";
  2. booking forces an account with a password first;
  3. the site says "across Pune", but only 6 areas are served, and bookings elsewhere are cancelled;
  4. a booked slot can't be changed, only cancelled.
- **The hidden rule:** ₹100 is taken off a technician's pay for each of his jobs that had to be redone (a free revisit within 7 days), in the week of the revisit.

## Fixed from it
- **A deduction taken off twice.** Gate 108 fixed adding a bonus twice; this is its mirror. The data prompts now cover deductions, fees and discounts too. Whenever an amount sits next to such a column, the query step shows a few rows with the amount, that column and its parts, so the answer can see which already includes which (`hive/access.py`).
  - **Re-asked:** 3 of 3 right (₹48,095, "already has the ₹900 taken off"), against 2 of 3 with only the wording change.
  - **Dabba Days' bonus question re-asked:** still right in 2 of 2 (₹1,71,820).
  - The re-asks are in `results/q10_rerun.json` and `results/q10_dabba_check.json`.

## Confounds
- One run, one simulated founder.
- The same author made both companies.
- The founder's brief says he is "happy to show typical prices up front". Gate 108's brief had a similar hint, so the two flights are alike, but it may help the price finding.
- The q10 fix was re-asked on the same data, not a fresh company.
