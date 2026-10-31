# Gate 67 results: does Hive get better the more one owner uses it? Nov 1 2026

**Question** (from the user, travelling: "something that will genuinely impact hive"). One business, three features built one after another. Does what Hive learns from the owner's reviews make later features need less of him, and come out more right?

**Answer.**
- **Not with the hand-over as the channel. Neither the ship nor the kill rule fired.** All four predictions failed.

| Features 2 and 3 pooled | House conventions right in the first build (of 21) | In what the second build got | Own decisions given (of 19) | Hidden pass | Rules he changed |
| --- | --- | --- | --- | --- | --- |
| F: nothing carried | 1 | 9 | 11 | 44.0% | 43 |
| M: standing rulings (as shipped) | 0 | 8 | 10 | 44.4% | 35 |
| C: rulings plus distilled house rules | 4 | 6 | 10 | 38.8% | 34 |

- **The distiller read the house correctly.** From feature 1's 32 corrections, one model call wrote house rules matching the hidden conventions in plain words:
  - "money is rounded up to the next whole cent, never to the nearest";
  - "a missing, blank or unreadable amount counts as 0";
  - "a boundary value belongs to the lower band";
  - "the day spills over into the following month".

  First builds given them got 4 of 21 convention decisions right, against 1 without.
- **But that did not survive to the end.** The judge found C's final sheets stated fewer conventions right (6 vs 9), and C's hidden pass was no higher. Each feature's own skim review and spot checks did most of the work in every arm. The second build's result was dominated by what the skimmer caught on that feature.
- **Hive's standing rulings carried nothing to new functions** (M: 0 of 21 first time). Their wording forbids stretching a ruling beyond its situation (Gate 41), and the code sheet found no repeats to leave out (0 in every feature). Every correction names one function.
- **Feature 3 was hard for every arm** (hidden 22–38%). Run-to-run noise is large: one build per arm per feature.

## Setup

- **The policy:** an independent rule-giver wrote one business's policy, a pet clinic. It has 15 functions in three features of 5, with 5 house conventions spanning all three features. The policy is published after scoring in `referee/oracle_g67.py`.
- **The owner:** the same skimming owner throughout. Builders could not ask him.
- **Each feature, in each arm:** a first build (3 builders), the code sheet, the list review, spot checks of every function, a judge's labels, then a second build (3 builders) scored on hidden tests. Its code was the next feature's start.
- Feature 1 was shared; F, M and C branched from feature 2.
- Predictions pushed before the run (`fb5407e`). Builders cost $7.04.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| C1 | C's first builds get ≥ 4 more conventions right than F's | **Failed:** +3 (4 vs 1) |
| C2 | M's first builds get ≥ 2 more than F's | **Failed:** −1 |
| C3 | C's hidden ≥ F + 5 | **Failed:** −5.2 |
| C4 | C's owner changes ≤ 0.7× F's | **Failed:** 0.79× (34 vs 43) |
| Ship / Kill | | **Neither fired** |

## Disclosed

The three arms ran in parallel threads, and the list review captures printed output by redirecting the whole process's output. On one owner screen (feature 3, arm C) one line of the driver's own log appeared among the rules. The driver's progress lines after feature 1 are missing from the run log; they went into the owners' screens or were lost. Rules from other arms' sheets did not appear on any owner screen beyond near-identical behaviours. The effect on the reviews looks small, but it is not zero. A rerun runs list reviews one at a time.

## What it means

1. **No product change.** Memory of the hand-over does not compound, as built.
2. **Gate 66 changed the question.** With today's model, builders who ask the owner beat the hand-over by 21–30 points. Compounding should be tested where intent actually flows: builders asking, with the answers kept. Do later features need fewer questions, and do the house rules from earlier answers make the first build right? That is Gate 69.

## Files

`prompts/` (rule-giver, house-rule and judge briefs; predictions), `referee/` (`run67.py`, `analyze.py`, the published policy).

`results/`:
- every feature's sheets, reviews, cases, corrections, judge labels and rulings/house rules in (`feature_*.json`);
- probes, agents and the run log.
