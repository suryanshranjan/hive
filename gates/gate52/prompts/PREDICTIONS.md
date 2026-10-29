# Gate 52 predictions: a flight test of the product

Registered Oct 30 2026, before the run. Overnight research. Gate 45 and the founder's Telegram are untouched.

## Why this test

Every gate since 39 measured one part of Hive in a wind tunnel. The founder will next steer a real build from his phone. Before he does, fly the whole product once, as shipped: `hive start` with no flags, the law choosing the team, the interview, the build, the owner's review of assumptions, and the code-sheet hand-over with its fix round. The owner is synthetic and answers every terminal prompt from a refund policy written in prose. The aim is to find what breaks before he does, and to measure what one owner gets end to end.

## Setup

- **Project:** Tiny Shop (`demo/`), a small order module with 2 passing tests. Goal: add `refund(order, days_since_delivery, reason)` in `shop/refunds.py`, returning the amount in whole rupees and the method.
- **The owner's policy:** 9 rules (windows of 14 and 30 days, damaged goods, shipping, final sale, a 50-rupee minimum, rounding, store credit, negative days). It sits in `private/g52/policy.md` and is published after scoring.
- **The judge:** 22 hidden acceptance tests written from the policy before the run and checked against a reference implementation (22/22). They are scored on the build as delivered (at the moment the code sheet is written) and on the branch after the hand-over.
- **The run:**
  - `hive.start.start(repo, goal=…, minutes=20)` with the real model and real builders.
  - The owner is a headless model that sees the terminal and types replies (`prompts/owner_brief.md`).
  - Hive's state starts empty: no Telegram, no memory.
- **Driver:** `referee/flight.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| P1 | It runs end to end and delivers a branch, with no crash | 70% |
| P2 | After the hand-over, ≥ 20 of 22 hidden tests pass | 50% |
| P3 | The hand-over does not make it worse: hidden after ≥ before | 75% |
| P4 | The owner is asked at most 40 times | 70% |
| P5 | The build costs at most $10 (builders, interview, sheet; the synthetic owner's own cost reported separately) | 70% |

Every product fault found is written up and fixed, whatever the predictions say.

## Limits

- One flight, one small feature, a synthetic owner who knows his policy and answers every prompt. A person reading 40 prompts is a different matter (Gates 30–38, 45).
