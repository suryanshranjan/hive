# Gate 85 predictions: the baseline, five live flights of the shipped flow

Registered Nov 2 2026, before the flights. The user: "the testing further should be exactly focusing on closing the gaps".

## Why this test

- **The founder's gaps** (`docs/gap_plan.md`): steady quality, under 10 minutes of his time, a bill that is mostly building.
- **None is measured over repeated runs.** Single flights scored 14 to 27 of 27, and asked the owner 22 to 71 prompts.
- **Wright-brothers rule:** measure the machine before changing it. This is the baseline every later gate in the gap plan is compared with.
- **Reliability is measured the way τ-bench does it:** pass^k, whether k independent tries all succeed (Yao et al. 2024).

## Setup

- **Five live flights of `hive start` as shipped** (Gate 84's flow), one after another, each from an empty `~/.hive`. Tiny Shop's three-part goal, the private policy and 27 hidden tests (`private/g54`), and the synthetic owner (Gate 54's brief).
- **One instrument added before the flights:** Hive's own model spend is now counted by the step that spends it (`explain.SPENT_BY`).
  - The spot checks' cost was never counted before. It is now, so this spend may read higher than in earlier gates.
- Driver `referee/flight85.py` (Gate 84's, plus the spend by step and the words the owner typed), analysis `referee/analyze.py`, both committed now.
- **A flight succeeds** if it ends without a crash, with one branch, and with ≥ 24 of 27 hidden tests passing.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| B1 | pass^1 ≥ 0.8 (at least 4 of 5 flights succeed) | 55% |
| B2 | pass^5 (all 5 succeed) | 30% |
| B3 | The median flight asks the owner more than 30 prompts | 60% |
| B4 | In every flight, Hive's own spend is ≥ 4× the builders' | 75% |

## Use

- These numbers are the baseline for Gaps 2, 3 and 5. Each failed flight will be labelled with MAST's failure modes (Gap 7).
- Whichever step spends most of Hive's own money is the first target of Gap 3.

## Limits

- One small project, with a synthetic owner whose answers never drift. Five flights estimate pass^1 only roughly.
- About $25 and about 75 minutes.
