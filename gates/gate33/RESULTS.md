# Gate 33 results: a model of the founder, tested on his held-out verdicts, Oct 28 2026

Only aggregate numbers are published. The founder's verdicts and the model's answers stay private.

**Question.** Can a model of this founder predict his decisions, including the surprising ones, well enough to stand in for him while Hive's review is tuned? The model was given his company's business and his own past verdicts with reasons.

**Answer: no. It predicts about a third of his surprising rules: better than a cold default, short of a stand-in.**

| Held-out gate | Surprising matched | Ordinary matched |
| --- | --- | --- |
| 30 (the deal's journey) | 2 / 6 | 3 / 4 |
| 31 (AI credits) | 2 / 9 | 3 / 3 |
| 32 (selection and invitations) | 3 / 5 | 5 / 7 |
| **All** | **7 / 20 (35%)** | **11 / 14 (79%)** |
| Cold default, for comparison | 0 / 20 (by construction) | about 100% |

Each gate was held out in turn: the model saw everything except that gate's verdicts. A blind judge (3 votes) compared each answer with his real verdict.

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| P1 | Matches ≥ 50% of his surprising verdicts | **Failed:** 35% |
| P2 | Matches ≥ 70% of his ordinary verdicts | **Held:** 79% |
| P3 | Overall ≥ 60% | **Failed:** 53% (18 of 34) |
| Kill | < 25% of surprising verdicts | **Did not fire** |

## What it means

1. **His surprising rules are mostly new in each area.** Knowing how he decided on deals and matching predicted only 2 of his 9 credit rules. A founder's style carries over a little; his specific rules do not. **The owner cannot be replaced by a model of the owner,** which is the premise Hive is built on, now measured.
2. **Learning his past rulings costs something.** On ordinary cases, the model's 79% is *below* the cold default's near 100%. Expecting him to be surprising, it sometimes invented surprises he does not have.
3. **What it is good for:** a hint about *where* he is likely to differ, which is the ranking signal the review already uses ("differs"). It is not a source of his answers.
4. **For tuning Hive:** a stand-in owner would tune the review to the model's habits, not his. Tuning stays with the real founder, about 15 minutes a gate.
