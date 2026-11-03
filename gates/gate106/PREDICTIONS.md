# Gate 106: predictions (registered before launch, Nov 3 2026)

**Question.** The owner gives only the business: "I want more creators signing up this month". Can Hive work out what to change in his product, and do it, with him only saying yes and deciding what only he can?

**Setup.**
- **The product:** a mock Sunny Shop Creators site (`shop/`: home, sign-up, dashboard, deals, invite and terms pages, 5 tests).
- **Three business goals:** more sign-ups (g1), more new creators reaching a first deal (g2), more invites (g3).
- **Planted problems:** each goal has 3 things in the product that hold it back. The list and its checks are private until scored. The starting product fails all 9 checks.
- **The flight:** driven through Jarvis exactly as from the phone. The plan is shown in plain words, he says one yes and answers his few decisions. Then step 1 is built and later steps are fix rounds on the same branch, each shown.
- **The simulated owner:** sends only the goal, taps "Yes, do it all", and answers questions from a private policy.
- **Arms:**
  - **A:** the planner (`hive/plan.py`).
  - **B:** the planner plus a simulated customer panel that reacts to the plan, after which the planner revises it. This re-implements an idea from MiroFish; its own repo never checks its predictions against reality.
- **Sample:** one flight per cell, 6 flights.

## Predictions

| # | Prediction | Fires if |
|---|---|---|
| J1 | The plan finds what holds him back | Arm A's plan addresses >= 2 of 3 planted problems on >= 2 of 3 goals (blind judge) |
| J2 | It gets built | Arm A's delivered product removes >= 2 of 3 on >= 2 of 3 goals (private checks), with all tests passing |
| J3 | His effort is a few taps | Median owner messages per goal <= 4 (the goal, one yes, at most 2 decisions) |
| J4 | He is asked only what only he can answer | >= 90% of questions judged owner-only, across both arms |
| J5 | Plain words | No more than 1 distinct technical word in all that Hive sends him in a flight, in >= 5 of 6 flights |
| J6 | The customer panel helps | B removes more planted problems than A in total (built), by >= 2 of 9. Else the panel stays off |
| J7 | Affordable | Each flight <= $5 and <= 40 minutes |

**What ships either way.** "Business in, plan out" ships if J1 and J2 hold. If they fail, it stays behind a confirmation and the failures go to the next gate. The panel ships only if J6 holds.

**Confounds:**
- n = 1 per cell.
- The planted problems are plain to see on purpose; a real product hides them better.
- The owner, the planner, the panel and the judge are the same model family.
