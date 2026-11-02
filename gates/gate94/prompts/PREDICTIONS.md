# Gate 94 predictions: a technical goal gets one builder's treatment

Registered Nov 2 2026, before any run.

## Why this test

- **Gate 89:** with no business decisions, the interview is skipped. But the reporter still answered a median of 21.5 prompts, from the review after the build (a code sheet of about 20 rules on ORM internals, then 9–24 spot checks), and the flow cost 14× one builder.
- **On these 10 Django issues one builder resolved 8 for $1.34** (Gate 86, F).

## The change (branch `dev93`, merged after Gate 91)

- **When the planner finds no business decisions in a goal, Hive also skips the business review.** It delivers with its tests and the interface check (which now runs before every delivery, from Gate 90's finding). Builders can still ask.
- **Also merged with it, ahead of the confirmation gate (Gate 93):**
  - at most 6 spot checks by default (Gate 88);
  - the interface check before every delivery.

  On a technical goal neither changes the flow, since there is no review.

## Setup

- **S3:** `hive start` with the merged code on Gate 86's 10 Django issues. Same reporter, harness and scoring (`referee/run94.py`, Gate 89's driver).
- Compared with S2 (Gate 89), S (Gate 86) and F (one builder, full issue).
- Analysis `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| T1 | S3's median reporter prompts ≤ 3 (the fast/cheap question, and any builder question) | 70% |
| T2 | S3 resolves ≥ 7 of 10 | 70% |
| T3 | S3's total cost ≤ 0.35× S2's | 65% |
| T4 | No delivery breaks a stated interface (read from the terminals) | 85% |

## Decision rules

- **Claim (T1, T2 and T3):** the change ships. For a technical goal, Hive costs about what one builder does.
- **T2 fails:** the review was catching real errors on technical goals. Keep a short review: the interface check and the 6 spot checks, no code sheet.

## Limits

- 10 issues, one run each, on a repository the models know. About $10.
