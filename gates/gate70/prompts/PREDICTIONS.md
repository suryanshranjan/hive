# Gate 70 predictions: overnight, questions saved for the morning against Hive's morning hand-over

Registered Nov 1 2026, before the run. It follows Gate 66 under the user's request while travelling ("go on and on"). Synthetic owner only.

## Why this test

Gate 66: a builder that asks the owner gets 85–93% of his rules, while Hive's hand-over of a build made without questions gets 63%, at 13× the owner's reading. But builders can only ask when he is there to answer. Overnight (`hive start --overnight`), Hive builds without questions and hands the build over in the morning, which is the weaker channel.

The alternative: overnight builders *record* their questions instead of asking. In the morning the owner answers the list, about 15 short questions in place of a 30,000-character review, and a fix build applies his answers.

## Setup

- **Rules:** two fresh rule sets from an independent rule-giver: g70a (seeds 70100, 70200000) and g70b (seeds 70300, 70400000).
- **The owner:** Gate 66's person model. He answers questions from his policy in a sentence or two, and skims when reviewing.
- **Arms:**

| Arm | What it is |
| --- | --- |
| **N0** | The overnight build as shipped: 3 builders, no owner, no questions |
| **QN** | The overnight build told to record a question for every open business decision (`referee/queue_question.py`), build its best guess, and keep going |
| **HV** | Hive's morning hand-over of N0 (code sheet, list review, spot checks of every function), then 3 fresh builders from the corrected sheet |
| **QA** | In the morning the owner answers every question QN recorded, one at a time; 3 fresh builders get his answers |

- N0 and QN build in stage 1; HV and QA in stage 2.
- **Owner load:** the characters of questions and answers (QA), or of the hand-over's screens (HV).
- The judge labels D, SL, HV, QA and R.
- Driver `referee/review70.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (means over the two runs)

| # | Prediction | Odds |
| --- | --- | --- |
| M1 | QA hidden ≥ HV + 10 | 60% |
| M2 | QA's owner reads ≤ 0.3× HV's characters | 70% |
| M3 | QA hidden ≥ QN + 15 (his answers fix the night build's guesses) | 60% |

## Decision rules

- **Ship:** M1 and M2 hold. Overnight builders record their questions; in the morning Hive sends him the list, on his phone or in the terminal, and a fix build applies his answers. The hand-over follows only if a later gate shows it still adds.
- **Otherwise:** the overnight path stays.

## Limits

- A synthetic owner whose answers never drift; one run per arm per rule set.
- QA's builders start fresh from the starting repo, as every sheet arm since Gate 42 has, rather than fixing QN's code.
- About $30.
