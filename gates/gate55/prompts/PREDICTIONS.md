# Gate 55 predictions: the skimming owner

Registered Oct 30 2026, before the rules exist. Overnight. Gate 45 (the founder's live review, day 2 pending) and his Telegram are untouched. This gate prepares for it.

## Why this test

Every wind-tunnel owner so far read every rule carefully. With such an owner, the code sheet took builders to 99.6% and 100% (Gates 42, 44). The founder is not that owner: on day 1 of Gate 45 he marked none of 46 rules, and he said a page of 8 rules was "so cluttered". Hive's answer was a conversational review: Jarvis says how each part works in a few sentences covering every rule, and the owner replies in his own words.

This gate breaks the "careful owner" assumption. The owner here skims: he reads each message once and corrects only what jumps out as clearly wrong for his business. The question: how much does the code sheet lose with such an owner, and does the conversational review recover it?

## Setup

- **Rules:** a fresh independent rule-giver (Gate 39's brief: 10 functions, 25 declared decisions). Hidden: 250 tests, seed 55200000, never committed.
- **The owner's knowledge:** his policy as plain prose rules, written from the oracle by a documenter. He holds them in his head; he never runs anything.
- **Stage 1:** N0 builds (3 builders). A describer writes what N0's code does as rules (D).
- **Three reviews of the same D**, each a separate session:
  - **CC:** a careful owner with the rule list in a terminal (`interview.confirm_sheet`, as in Gates 42 and 44).
  - **CS:** a skimming owner with the same rule list.
  - **CT:** the same skimming owner on the phone, in Hive's conversational review: sections by area, "why it matters", Jarvis's summary covering every rule, his replies read in his own words. It is driven through a chat channel whose other end is the synthetic owner.
- **Stage 2:** fresh builders from each reviewed sheet (CC, CS, CT; 3 each).
- **Judge:** labels D, CC, CS, CT and R per declared decision, before the stage-2 builds.
- **Driver and analysis:** `referee/review55.py`, `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| S1 | The careful list review repairs ≥ 80% of D's wrong or partial decisions (Gate 42: 89%) | 75% |
| S2 | The skimming list review repairs ≤ 50% | 55% |
| S3 | The skimming owner repairs ≥ 15 points more in the conversation than with the list | 40% |
| S4 | Hidden pass: CT ≥ CS + 5 points | 40% |
| S5 | Hidden pass: CC ≥ 95% (Gates 42, 44: 99.6%, 100%) | 70% |

## Decision rules

- **S2 fails with CS ≥ 0.80:** the skimming brief did not change the synthetic owner's behaviour, and this gate says nothing about attention. Report it as such.
- **S3 and S4 hold:** the conversational review is the right format for an owner who skims. Keep it as the default on the phone and consider it in the terminal too.
- **S3 fails** (the conversation repairs no more): its value is comfort, not correctness. The next lever is fewer rules to read: show only those where the code made a business choice.

## Limits

- A synthetic owner told to skim is a model of a busy person, not one. The founder's own review (Gate 45, day 2) is the real test.
- One run per team; about $15.
