# Gate 106: results (flown Nov 3 2026, lab container on the user's laptop)

**Question.** The owner gives only the business ("I want more creators signing up this month"). Can Hive work out what to change and do it, with him only saying yes and deciding what only he can? (Predictions: `PREDICTIONS.md`, pushed before launch in `2d6096d`.)

**Answer (established for this mock product, n = 1 per cell).** Yes.
- **Found:** with only the business goal, Hive's plan found **8 of 9** planted problems.
- **Fixed:** it built and removed the same **8 of 9**, with every test passing.
- **His effort:** 4 messages (the goal, one yes, 2 decisions), every question one only he could answer, no technical words.
- **Time and cost:** 2-4 minutes and $0.88-1.45 per goal.
- **The miss:** a reward that exists only in his payouts, never on the site. Hive cannot find what the product doesn't show.
- **The customer panel** (MiroFish's idea, re-implemented) **did not help:** 8 of 9 either way, at about 1.5x the planning cost. It stays off.

## The numbers

| Goal | Arm | Plan found | Built | Owner messages | Questions (owner-only) | Technical words | Screens sent | Tests | Minutes | Cost |
|---|---|---|---|---|---|---|---|---|---|---|
| g1 more sign-ups | A | 3/3 | 3/3 | 4 | 2 (2) | 0 | 3 | 9/9 | 2 | $0.88 |
| g1 | B (panel) | 3/3 | 3/3 | 4 | 2 (2) | 0 | 3 | 8/8 | 3 | $1.17 |
| g2 more first deals | A | 2/3 | 2/3 | 4 | 2 (2) | 0 | 4 | 12/12 | 3 | $1.13 |
| g2 | B (panel) | 2/3 | 2/3 | 4 | 2 (2) | 0 | 4 | 15/15 | 4 | $1.45 |
| g3 more invites | A | 3/3 | 3/3 | 4 | 2 (2) | 0 | 4 | 25/25 | 3 | $1.24 |
| g3 | B (panel) | 3/3 | 3/3 | 3 | 1 (1) | 0 | 3 | 15/15 | 3 | $1.18 |

- **Planning:** $0.21 (A), $0.43 (B).
- **Minutes:** checked against file times. These are small static pages, so each step after the first is a fix round of about a minute.

**What the plans said (A, in the words he saw):**
- **g1:** "A shorter sign-up form", "A home page that speaks to creators", "Make the ₹500 invite reward easy to see".
- **g2:** "A shorter sign-up form", "Show open deals right after sign-up", "Make the Apply button actually do something", "Tell creators upfront what they can earn".
- **g3:** "A working invite page that shows the ₹500", "Put the invite link where creators look", "A shorter sign-up for invited friends", "Welcome invited friends with what they'll earn".

**His questions** (all judged owner-only). Example: "May the homepage say 'Creators earn about ₹8,000 a month in their first 3 months'? That reads as a promise to new creators."

**The one miss (g2, both arms):** "the ₹500 first-deal reward is never mentioned to a new creator". That reward exists only in his payouts (the private policy); nothing in the product shows it. Neither the planner nor the panel could know.

## Predictions scored

| # | Prediction | Result |
|---|---|---|
| J1 | A's plan addresses >= 2 of 3 on >= 2 of 3 goals | **Held:** 3, 2, 3 |
| J2 | A's product removes >= 2 of 3 on >= 2 of 3, all tests passing | **Held:** 3, 2, 3; all passing |
| J3 | Median owner messages <= 4 | **Held:** 4 (3-4) |
| J4 | >= 90% of questions owner-only | **Held:** 11 of 11 |
| J5 | <= 1 technical word per flight in >= 5 of 6 | **Held:** 0 in all 6 |
| J6 | The panel removes >= 2 more of 9 | **Failed:** 8 vs 8. The panel stays off (`HIVE_PLAN_PANEL=1` to try it) |
| J7 | <= $5 and <= 40 minutes per flight | **Held:** $0.88-1.45, 2-4 min |

**Found while flying:**
- **Lab fault (the first g1A):** the flight started the agreed plan a second time while Jarvis's own thread had already started it. Two step-1 builds collided. The flight was fixed (`5b30571`) and g1A was flown again from scratch.
- **Gap:** the step-1 builder wrote down 3 business questions. In these flights (no phone) nobody answered them; on the phone, Hive sends them to him after the step lands. This was not measured here.
- **Wording:** "I'll put 1 builders on it" in the build's own log. Fixed.

## What it changes in Hive

- **Ships:** business in, plan out (J1, J2 held). A business goal from the phone goes to `assistant.pursue`, then `hive/plan.py`, then `run_plan`.
- **Not shipped:** the customer panel (J6).
- **Next:** what the product doesn't show, Hive can't find. Candidate, untested: the plan asks one more question when the goal touches money or promises: "Is there anything you offer creators that the site doesn't say yet?"

**Confounds:**
- n = 1 per cell.
- The planted problems are plain to see on purpose.
- One model family plays the owner, the planner, the panel and the judge.
- Static pages, so builds are fast; a real product's steps will take longer.

**Files:**
- `results/<g><arm>.json`: the plan, his messages, everything Hive sent, cost and minutes;
- `results/<g><arm>_product/`: the delivered product;
- `results/summary.json`.

The planted problems, their checks and the owner's policy stay in `private/g106` on the lab.
