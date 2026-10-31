# Gate 68 predictions: when builders can ask the owner, does the swarm match one agent, and does the hand-over still add?

Registered Nov 1 2026, before the run. It follows Gate 66's registered rule ("if CQ ≥ HV: next, test them combined"), under the user's request while travelling.

## Why this test

Gate 66's first run (g66a): one Claude Code builder that asked the owner reached 88.8% hidden (11 questions unprompted) and 93.2% (20 questions, told to ask first). Hive's hand-over of a build made without questions reached 55.6%, and no owner 35.2%. With today's model, a builder that asks gets nearly all of an owner's rules, provided the owner answers from his policy.

Hive as shipped also lets builders ask the owner whenever he is present (`hive ask`). Gate 66's Hive arm had only the hand-over, so two questions decide Hive's design:
1. Does Hive's swarm, asking, match one agent asking?
2. Does the hand-over (code sheet plus spot checks) still add anything after a build in which the builders asked?

## Setup

- **Rules:** two fresh rule sets from an independent rule-giver: g68a (seeds 68100, 68200000) and g68b (seeds 68300, 68400000).
- **The owner:** Gate 66's person model, an owner on call answering from his policy in a sentence or two. The skimming brief is used for the hand-over.
- **Arms:**

| Arm | What it is |
| --- | --- |
| **CQ** | One builder, told to ask the owner about every business decision the spec leaves open before building it (Gate 66's best arm) |
| **SQ** | Hive's swarm with the same instruction: 3 builders, one owner on call for the team. They read every answer so far before asking (`ask_owner.py --answers`, like `hive answers`) |
| **SQH** | Hive's hand-over of SQ's build, as shipped after Gate 63 (the code sheet, list review, then spot checks of every function), then 3 fresh builders from the corrected sheet |

- CQ and SQ build in stage 1; SQH in stage 2.
- Driver `referee/review68.py` (from Gate 66's), analysis `referee/analyze.py`, both committed now.

## Predictions (means over the two runs)

| # | Prediction | Odds |
| --- | --- | --- |
| Q1 | SQ hidden ≥ CQ − 3 | 60% |
| Q2 | SQH hidden ≥ SQ + 3 (the hand-over adds after a build whose builders asked) | 35% |
| Q3 | SQ asks ≤ 1.5× as many questions as CQ (the team shares answers) | 55% |

## Decision rules

- **If Q2 fails:** after a build in which the builders could ask the owner, Hive skips the long hand-over. It stays for builds he could not answer, such as overnight builds.
- **If Q2 holds:** keep both.
- **If SQ < CQ − 5:** the swarm loses intent when it asks. Look at how answers spread between builders before anything else.

## Limits

- A synthetic owner answers consistently from his policy; a real founder does not (Gates 36–38).
- One run per arm per rule set; about $35.
