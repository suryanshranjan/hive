# Gate 4 results: planned questions vs free questions, Oct 27 2026

**Question.** With the same budget of 30 questions to a product owner, does a planner do better than letting the builders ask freely? The planner chooses questions to cover every function's uncertain input types and turns every answer into a shared test.

**Answer: no.** The planned team scored 76.4% on the hidden tests and the free-asking team 76.8%. That is a difference of −0.4 points, with a paired 95% interval of −12 to +11 points. The registered kill condition fired. Both teams with questions beat the team with none by 29 points, the same gain as in Gate 3.

## Setup

- **Rules:** a fresh set of 20 invented business rules (`referee/oracle.py`, sealed until scoring), added to the same engine as Gate 3.
- **Teams:** three teams of 3 builders, one run each.
  - **R0:** no questions.
  - **R30:** the builders share 30 questions and ask them freely.
  - **P30:** a planner agent spends the 30 questions first and the builders cannot ask. The planner writes a coverage plan (`results/planner_PLAN.md`), gives every function at least one question, and turns each answer into a test.
- **Hidden tests:** 500 (seed 4200000), 70% edge-case calls; never seen by any agent.
- **Registration:** predictions were pushed to GitHub before launch (commit 571bf21).

| Team | Questions | Values answered | Tokens | Visible | Hidden tests | 95% CI by function | Edge calls right | Happy-path calls right |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R0 | 0 | 0 | 320k | 1,380/1,380 | **239/500 (47.8%)** | 37.6–58.8% | 65.5% | 100% |
| R30 | 30 (2 functions never asked) | 90 | 325k | 1,380/1,380 | **384/500 (76.8%)** | 64.8–88.2% | 85.1% | 100% |
| P30 | 30 (all 20 functions asked) | 90 | 434k (planner 115k) | 1,410/1,410 | **382/500 (76.4%)** | 66.2–86.0% | 86.0% | 100% |

Paired differences, bootstrapped over the 20 functions:

| Comparison | Difference | 95% CI |
| --- | --- | --- |
| R30 − R0 | +29.0 points | +15 to +43 |
| P30 − R0 | +28.6 points | +15 to +42 |
| P30 − R30 | −0.4 points | −12 to +11 |

How we know the scores are right:

- Two scorers agree exactly: a replay of every commit, and a call-by-call probe of each final engine.
- No team broke any existing test at any commit.
- All 30 of the planner's answer-tests match the private rules.

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| G1 | All visible examples pass; P30 also passes the planner's tests | **Held** |
| G2 | P30 ≥ R30 + 5 points | **Failed**: −0.4 points |
| G3 | P30 ≥ 95% | **Failed**: 76.4% |
| G4 | Replication: R0 in 45–70%, R30 in 78–92% | **Half held**: R0 47.8% is in range; R30 76.8% is just below |
| G5 | P30 asks about all 20 functions; R30 leaves at least 3 unasked | **Half held**: P30 asked about all 20; R30 left only 2 unasked |
| Kill | If P30 ≤ R30, coverage planning does not help | **Fired.** The claim from Gate 3, that *which* questions matter more than *how many*, is not supported at a 30-question budget. |

## Why planning did not help

1. **Neither team found where the owner breaks convention.** In both teams with questions, 51 to 56% of the remaining errors fall into two kinds of rule:
   - **NULL handling (24 to 30% of the errors).** Six functions do not return NULL for NULL input. For example, `band(NULL)` is 'none', and a NULL tier means full price. Each team spent only 3 of its 30 questions with NULL in them. Builders assumed SQL's usual "NULL in, NULL out".
   - **Caps at extremes (26 to 27%).** The discount is capped at 50, points at 1,000, an age of 150 or more is NULL, and a parcel over 30 kg is NULL. The planner had listed "very large values" and NULL as open, but at low priority. It spent its questions on thresholds that looked ambiguous, which is what the free askers did too.
2. **An answer pins down a point, not a rule.** Builders turn a few answered values into a rule, and sometimes pick the wrong one:
   - From `ELAPSED(-5) = '-5s'` and `ELAPSED(100) = '0:01:40'`, a P30 builder concluded that negatives use seconds. It missed that everything under a minute does.
   - Builders also carried rulings across functions. `GRADE_POINT('E') = 0.0` became "unknown grades are 0.0". The rounding rule for `ROMAN` and `COLOR_HEX` was applied to `ORDINAL` and `ELAPSED`, which don't round.
   - These cost P30 about 45 of its 139 failing calls.
3. **Spreading questions evenly took them away from hard functions.** P30 gave 12 functions one question each. R30 put 4 questions on `ELAPSED` (100% right) where P30 put 1 (63%).
4. **Where planning did help:**
   - `WEEKDAY`: 100% vs 58%, by finding the lowercase 'sat'/'sun'.
   - `MEDIAN3`: 90% vs 69%.
   - `BAND`: 83% vs 60%.
   - `VOWELS`: 88% vs 72%.

   The losses roughly cancel these.

## What this changes

- **Replicated:** 30 questions buy about 29 points of hidden correctness, on two different rule sets: +28.6 in Gate 3 and +29.0 here. Starting levels differ (58% vs 48% with no questions), so absolute numbers are not constants.
- **Not supported:** that planning the questions beats free asking at the same budget.
- **New hypotheses (untested):**
  - The owner's surprises sit where the rule departs from a convention the questioner takes for granted: NULL handling, caps, unknown values. Those are exactly the places nobody thinks to ask, so a strategy that asks about the defaults one assumes may beat both teams.
  - Every answer should be stored as a ruling about one input, so that builders don't stretch it into a general rule.

  Both hypotheses were formed after looking at this rule set, which I wrote. They need a fresh rule-giver to test fairly.
- **Cost:** planning added one agent (+34% tokens) and ran before the builders, so P30 took 12 minutes against R30's 4.5.

## Limits of this test

- One run per team; the intervals above cover variation across functions, not across repeated runs.
- P30 changed three things at once (allocation, coverage-driven choice, answers as shared tests), so a null result cannot be attributed to any one of them.
- I wrote both rule sets. Their surprises reflect one rule-giver's habits.

## Files

| Path | Contents |
| --- | --- |
| `referee/oracle.py` | The 20 private rules, unsealed after scoring |
| `referee/gen4.py` | Visible and hidden test generator |
| `referee/probe.py` | Call-by-call scorer |
| `prompts/` | Builder and planner prompts; predictions registered before launch |
| `seed.bundle`, `swarms/` | Starting repo and the three teams' full histories |
| `results/asks_*.log` | Every question and answer |
| `results/planner_PLAN.md` | The planner's coverage plan and what it learned |
| `results/eval_*`, `results/probe_*` | Per-commit replays and per-call scores |
| `results/tokens.csv` | Tokens per agent |
