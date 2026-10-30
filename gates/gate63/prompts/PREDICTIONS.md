# Gate 63 predictions: spot checks on the parts the list review touched, too

Registered Oct 30 2026, before the run. A follow-up to Gate 60 under the user's "Run the tests as required". Synthetic owner only; Gate 45 and the founder's Telegram are untouched.

## Why this test

Hive's hand-over (Gate 58) shows spot checks only for the parts the owner's rule-list review left as they were. The idea was not to re-ask what he had just looked at.

In Gate 60's fresh rule set, the skimmer corrected one headline rule in every function, so he was shown no spot checks at all. Yet the details he skims past (rounding, odd inputs, exact cut-offs) are where Gate 58's spot checks gained, and a part he touched for its headline rule still has its details unchecked.

## Setup

This gate is built from Gate 60's own records: the same N0 build, sheet D, spotter cases, owner brief and policy.
- **g60a** (Gate 55's rules): the list touched 4 of 10 functions. **CA** = CB's sheet, then the spot checks of those 4 functions (the ones Gate 60 skipped).
- **g60b** (the fresh rules): the list touched all 10, so CB equals SL. **CA** = SL's sheet, then the spot checks of all 10 functions.
- Each correction is applied on its own and re-shown (Gate 58's machinery, `gates/gate60/referee/review60.py`).
- A fresh judge labels SL, CB, CA and R together.
- 3 fresh builders build CA from Gate 60's starting repo. Its hidden pass is compared with Gate 60's CB and SL builds on the same hidden suite.

Driver `referee/review63.py`, analysis `referee/analyze.py`, both committed now.

## Predictions (pooled over both runs, 50 declared decisions)

| # | Prediction | Odds |
| --- | --- | --- |
| H1 | CA states ≥ 3 more decisions right than CB | 50% |
| H2 | Hidden CA ≥ CB + 3 points (mean over the runs) | 45% |
| H3 | CA spoils at most 1 decision CB had right | 70% |
| H4 | The skimmer corrects ≥ 20% of the touched-part cases | 55% |

## Decision rules

- **Ship:** H1 and H2 hold. Hive's spot checks cover every part, touched or not.
- **Kill:** CA is no better than CB on decisions and on hidden. The skip rule stays.

## Limits

- CA's stage-2 build is new, while CB's and SL's come from Gate 60, so builder noise enters the hidden comparison. In g60b, two builds of the same sheet (SL and CB) differed by 2.8 points.
- One synthetic skimmer; about $12.
