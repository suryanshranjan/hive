# Gate 69 predictions: does Hive need less of the owner the more he uses it, when builders ask?

Registered Nov 1 2026, before the run. It follows Gates 66–68 under the user's request while travelling ("hive needs to surpass everything … go on and on"). Synthetic owner only.

## Why this test

- **Gate 66:** builders that ask the owner get 85–93% of his rules.
- **Gate 68 (first run):** Hive's swarm asking matched one agent asking (96.8% each).
- **Gate 67:** what Hive kept from the owner's reviews did not carry to new functions.

So a lone agent and Hive's swarm are now level on one feature. The edge Hive can have over a one-shot agent is across features: one owner, one business, week after week. If Hive keeps every answer, and distils house rules from them, later builders should need to ask him less, while staying as right.

## Setup

- **The business:** Gate 67's (a pet clinic; 15 functions in three features of 5, 5 house conventions), published after Gate 67. New draws (seeds 69101–69103, 69200000–69400000).
- **The owner:** Gate 66's owner on call, answering from his policy in a sentence or two (Gate 68's server, which also lists the answers given so far).
- **Builders:** 3 per build, told to ask him about every open decision before building each function, and to read the answers already given (Gate 68's SQ).
- There is no hand-over; each build's hidden pass is scored directly.
- **Feature 1** runs once, shared. From feature 2 on, each arm has its own owner on call:

| Arm | What later builds get |
| --- | --- |
| **F** | Nothing from earlier features. This is Hive as shipped: `hive answers` lists one build's answers |
| **M** | Every earlier answer, as the owner's standing answers to read before asking |
| **C** | M, plus house rules distilled from all earlier answers ("Across the business: …"), applied to new functions |

Driver `referee/run69.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (features 2 and 3 pooled)

| # | Prediction | Odds |
| --- | --- | --- |
| A1 | C asks ≤ 0.7× as many questions as F | 50% |
| A2 | M asks ≤ 0.85× as many as F | 45% |
| A3 | C's hidden pass ≥ F's − 2 (no loss) | 65% |
| A4 | C's hidden pass ≥ F's + 3 | 30% |

## Decision rules

- **Ship:** A1 and A3 hold. Hive keeps every answer the owner gives for later builds of the project, distils house rules from them, and builders read both before asking.
- **Kill:** C asks more than 0.85× F's questions. Nothing compounds.

## Limits

- One business, one build per arm per feature, and a synthetic owner whose answers never drift.
- About $15.
