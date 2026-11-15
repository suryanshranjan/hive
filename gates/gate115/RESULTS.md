# Gate 115: results (flown Nov 15 2026, the owner's Windows laptop, real Claude, simulated founder)

**Question.** Does Hive find what lives only in the founder's head before it plans? (Predictions: `PREDICTIONS.md`, pushed before launch in `64063c9`.)

**Answer.** With a simulated founder (model, not established for a real one): asking up to 3 specific questions about what the plan assumes, instead of one, made the final plan account for the hidden fact in **8 of 8** runs against **4 of 8**. The cost was the same ($0.88 a run either way) and the time was 11 s longer (1.77 vs 1.58 min a run). By the registered rule, `three` is now Hive's default.

The gain is real but inflated: the simulated founder volunteered his other hidden facts once asked about capacity, and the arm that asks more questions collects more of that. See "Confounds" below.

## The numbers (2 runs per goal per arm, 22 runs, no errors)

| Goal | `one`: accounts / surfaced | `three`: accounts / surfaced | `three`'s questions found it how |
|---|---|---|---|
| G1 Class 10 sign-ups (Class 10 full till April) | 2/2, 2/2 | 2/2, 2/2 | Asked about Class 10 room directly |
| G2 more families via schools (20% partner-school deal) | 2/2, 2/2 | 2/2, 2/2 | Asked about school tie-ups directly |
| G3 the fees page (Hindi-medium ends Dec 31) | **0/2**, 0/2 | **2/2**, 2/2 | Asked "do you have enough tutors…"; he volunteered Hindi ending (partly leakage) |
| G4 drop-off after the demo (junior demo tutor, then a different one) | **0/2**, 0/2 | **2/2**, 2/2 | Asked "what reason do families give: the price, the tutor…" and "does the demo tutor stay on?" (targeted) |
| **G1-G4** | **4/8**, 4/8 | **8/8**, 8/8 | |
| G5 held out: Gachibowli and Kondapur (no weekday evening visits) | 2/2, 2/2 | 2/2, 2/2 | Both asked whether tutors travel there |
| C1 control: the FAQ (nothing hidden) | 1 question, 3 steps | 3 questions, 4 steps | |

- **Questions asked:** `one` 1.0 a goal; `three` 3.0 every time (never fewer).
- **Cost:** $9.62 for 11 `one` runs and $9.65 for 11 `three` runs, about $0.88 a run including the founder and the judges. **Over the registered estimate:** $19.27 in all, against $8-15.
- **Time:** mean 1.58 min a run for `one` (1.4-1.8), 1.77 min for `three` (1.6-2.0).
- **What `one` asked on G3 and G4:** whether the board-prep batches cost the same; whether families get a discount for their first month. Both were reasonable, and neither was near the fact.

## Predictions scored

| # | Prediction | Result |
|---|---|---|
| P1 | `one` ≤ 4 of 8 (G1-G4) | **Held:** 4 of 8 |
| P2 | `three` ≥ 7 of 8, at least 3 more than `one` | **Held:** 8 of 8 (+4) |
| P3 | `three` surfaces ≥ 7 of 8; `one` ≤ 4 of 8 | **Held:** 8 and 4 |
| P4 | Held out (G5): `three` 2 of 2; `one` ≤ 1 of 2 | **Half held:** `three` 2 of 2, but `one` also 2 of 2. The held-out goal named the area, so either way of asking reached it. It does not test fitting; that test still needs a second company written by someone else |
| P5 | `three` ≤ 3 questions, mean ≤ 3.0; on the control ≤ 2 questions and ≥ 2 steps | **Failed in part:** mean 3.0 and ≤ 3 held, and the control kept 4 steps. But it asked 3 on the control, where nothing was hidden: it always asks the full 3 |
| P6 | No invented business facts in `three`'s final plans | **Held:** checked by hand and by keyword (Class 10, April, 20%, the schools, Hindi, Dec 31, junior tutor, the areas, 22 tutors) on all 10 G1-G5 runs; every fact is on the site or in his answer |

**Decision rule:** P2 held and P4 was not killed, so `three` is the default (`hive/plan.py` `ASK_DEFAULT = 'three'`).

## Confounds (stated plainly)

1. **The simulated founder over-shares.** His brief says to answer plainly when a question touches a fact. In `three` runs he stated 1 to 5 of his 5 hidden facts per answer, about 3 on average; in `one` runs about 1. On G3, the win came from a capacity question, which he answered with everything he knew. A real founder may answer "yes, we have tutors" and stop. **G4's win is the cleanest:** the questions there named the cause.
2. **I wrote both the prompt and the facts.** The list of places to look (capacity, off-site deals, start/stop, the real reason people leave, who does what) maps onto G1-G4. G5 was meant to test this, but it did not separate the arms (P4).
3. **One company, n = 2 a cell, one judge model.** The judge is blind to arm and question, but it is the same model family.
4. **Burden.** `three` always asks 3 questions in one message, even when nothing is hidden (C1). That goes against "ask only when needed". Next on this thread: let the planner ask fewer when its plan rests on what it saw, and measure it on the control.

## What it changes in Hive

- **The planner asks up to 3 specific questions** about what its plan assumes and nothing it saw can confirm, in one numbered message. His one answer is kept for every later plan, and the plan is made again with it. Before, it asked one question when it suspected something. `hive/plan.py` (`ASK_THREE`, now the default; `HIVE_PLAN_ASK=one` brings back the old behaviour); `hive/assistant.py` pursue; `tests/test_brief.py`.
- **Not changed:** nothing in onboarding. The answers already go into memory, so every later plan uses them.

**Files:**
- `results/runs.json` (every run: the questions, his answer, the first and final plan, the verdicts, the cost);
- `results/run.log`.

The private inputs are in `private/g115/`: the site generator and the founder's brief with the hidden facts. They hold no real company and can now be published.
