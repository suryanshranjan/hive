# Gate 30 results: the founder's surprising rules, review vs no owner, Oct 28 2026

Only aggregate numbers are published. The company (Company X), its spec, code, situations, the founder's verdicts and choices stay private.

**Question.** On cases where the founder differs from what a builder would do by default, does his phone review of the builders' assumptions (2 or 3 alternatives per decision, Hive's suggestions off) carry his rules into the code?

**Answer: partly. For the first time, owner input moved a surprising rule into the code, but by far less than predicted.**
- **Arm R (after his review) passed 3 of 6 surprising cases; arm N (no owner) passed 2 of 6.** That is +17 points. The prediction was ≥ +30; the kill condition was < +10.
- **Why not more:**
  - The builders recorded an assumption touching **all 6** surprising rules, but only **3** of them ranked into the 8 decisions shown to him first. He left the other 32 as built.
  - Of the 3 he saw, 1 already passed, 1 he corrected to his rule, and 1 he answered *differently from his own confirmed verdict an hour earlier*. His free-text rule was not among the alternatives offered, and he picked one that was.

## Setup

- **Codebase.** The private, secret-checked copy of a real company's Node.js backend, on a clean base. The company's repository was never pushed to.
- **How the cases were made** (all on Telegram):
  1. The founder described the journey of a deal.
  2. The experimenter wrote 12 situations along it.
  3. The founder gave verdicts by phone.
  4. A fresh model answered the same situations cold (3 runs, unanimous on 10 of 12).
  5. A blind judge (3 votes, not told whose answer was whose) labelled 6 cases surprising, 4 ordinary and 2 unclear.
  6. The founder confirmed the experimenter's reading of all 6 surprising verdicts.
- **Feature.** A pure deal-policy library with a fixed interface (12 situations, enumerated decisions).
- **Arms, from one shared build:**
  - **N** is the build before any owner input: 4 workers, no questions, assumptions recorded.
  - **R** is the same build after the founder's phone review and one fix round.
- **Predictions** were pushed before the build (commits 4e139bc, 6b3de1f).

| Measure | Arm N (no owner) | Arm R (after his review) |
| --- | --- | --- |
| **Surprising cases** | **2 / 6** | **3 / 6** |
| Ordinary cases | 3 / 4 | 3 / 4 |
| Existing backend tests | 384 / 384 | 384 / 384 |
| All tests on the final branch | 420 / 420 | 437 / 437 |
| Cost | $3.20 (build) | + $3.17 (fix round) |

| The review | |
| --- | --- |
| Business assumptions recorded | 40 (plus 4 technical, for engineers) |
| Shown first / left as built | 8 / 32 |
| Founder's choices on the 8 | 7 changed, 1 kept, about 7 minutes in all (13 s to 3 min each) |
| Surprising rules with any matching assumption | 6 of 6 |
| …that reached the 8 shown | 3 of 6 |

## Predictions scored

| # | Prediction | Result |
| --- | --- | --- |
| S1 | On surprising cases, R beats N by ≥ 30 points | **Failed:** +17 (3/6 vs 2/6) |
| S2 | On ordinary cases, both arms ≥ 85% | **Failed:** 75% each (3/4) |
| S3 | Existing backend tests pass in both arms | **Held** |
| S4 | Review under 10 minutes; at least one change per 3 surprising cases | **Held:** about 7 minutes; 7 changes |
| S5 | No secret-like file; no breaking commit left broken | **Held** |
| Kill | R beats N by < 10 points | **Did not fire** (+17) |

## What it means

1. **The first measured gain from the owner on surprising rules.** After three ties (Gates 27 to 29), the review moved one of the founder's surprising rules into the code that the builders had not reached alone. That is the case Hive exists for. The effect is real but small: one case in six, one run.
2. **The bottleneck is the ranking, not the builders.** Builders recorded an assumption for every surprising rule, but the ranking, by how much each decision matters to customers in the model's view, put three of them below the top 8. **What an owner most needs to see is where he differs from the default, and the default's own judgement of importance does not find that.** Ways to fix it:
   - show more decisions in faster form;
   - group them so related ones are judged together;
   - rank by the owner's own past rulings and topics he cares about (the memory of rulings can supply these).
3. **A menu of options frames the rule.** With suggestions off, the founder still chose from what was offered. On one surprising rule, his free-text verdict was not among the alternatives, and he picked a different rule from the list, contradicting his own confirmed verdict an hour earlier. Alternatives make disagreeing easy, but only within the menu. Before showing a menu, the review should ask an open "what should happen?" for high-stakes decisions, or include a free-text-first mode.
4. **Owners are not perfectly consistent over an hour.** Hive should check new answers against the owner's earlier rulings, the same way it now checks for contradictions within one review.

## Limits

- One founder, one feature, one shared build.
- 6 surprising cases, so one case is 17 points.
- The situations and the readings of the founder's free-text verdicts were written by the experimenter. The founder confirmed the readings.
- Arm R had a fix round that arm N did not.
- The interface listed the allowed decisions, which may have helped both arms on ordinary cases.

## Files

| Path | Contents |
| --- | --- |
| `prompts/PREDICTIONS.md` | Design, predictions and the pre-build amendment |
| `RESULTS.md` | This file (aggregates only) |
