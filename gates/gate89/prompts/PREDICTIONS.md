# Gate 89 predictions: no business decisions, no interview

Registered Nov 2 2026, before any run.

## Why this test

- **Gate 86:** on real Django bug reports, `hive start`'s owner interview invented a business to ask about ("A customer pays Rs 5,000 for an order, then cancels…"). The reporter answered "I don't have that information" 96 times.
  - The flow cost 15× one builder, with a median of 23.5 prompts, and resolved no more.
- **The cause, in the code:**
  - The planner (`interview.decisions`) is told to list business decisions. When it found none, `write_situations` still asked the model for 12 "situations where his own business rules are most likely to matter".
  - When it found some, it turned technical behaviour into business analogies.

## The change (in `hive/interview.py` and `hive/start.py`; developed on branch `dev89`, merged only after Gates 87–88 finish, so they run unchanged code)

1. The planner is told that a technical fix or change, with no rule an owner sets, has no business decisions.
2. With no business decisions, there are no interview questions: `hive start` says so and starts the builders, who can still ask.

Unit test: no decisions, no questions.

## Setup

- **S2:** Gate 86's arm S again, on the same 10 Django issues with the same reporter and harness (`referee/run89.py`, Gate 86's driver with the arm added).
- **Planner check** (`referee/plan89.py`): `interview.decisions` called 3 times on each of the 10 issues' summaries and on two business goals (Tiny Shop's three-part goal; a late-fee and reminder goal). Run with the changed code.
- Analysis `referee/analyze.py` (compares S2 with Gate 86's S), committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| K1 | S2's median reporter prompts ≤ 8 (S: 23.5) | 65% |
| K2 | S2 resolves ≥ 7 of 10 (S: 8) | 75% |
| K3 | S2's total cost ≤ 0.4× S's | 55% |
| K4 | The planner finds ≥ 5 decisions in every call on both business goals | 80% |
| K5 | No interview on ≥ 8 of the 10 issues | 70% |

## Decision rules

- **Claim (K1–K4):** the change ships.
- **K4 fails:** the planner now misses business decisions. Do not ship; narrow the wording.
- **K1 fails while K5 holds:** the remaining prompts come from the review after the build. That is the next target.

## Limits

- 10 issues, one run each. The two business goals are checked through the planner only, not full flights.
- About $15.
