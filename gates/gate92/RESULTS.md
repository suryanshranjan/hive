# Gate 92 results: when the owner changes his mind (Gap 5), Nov 2 2026

**Question.** Hive keeps every ruling an owner gives and tells the next build to follow them and "not ask again". When his rules change and he says so, does that memory make the old rules stick?

**Answer.**
- **No: memory did not make the old rules stick.** With the day-1 rulings kept (arm M), day 2's builds scored 29, 28 and 29 of 29 on the new policy. Without them (arm F) they scored 29, 29 and 29. D2 failed, which is the good outcome.
- **Why:** Hive's interview noticed that the owner's new answers pulled against his old rulings, and asked which one holds now:

  "One thing: this answer pulls against an earlier ruling of yours. … 1 point per full ₹100 …, or 1 point per full ₹50 …? Which holds now?"

  He picked the new rule, and the latest word won. This happened 2 to 5 times per flight.
- **Memory saved no prompts:** M asked a median of 51 against F's 45 (D3 failed). The settling questions cost more than memory saved.

| Day 2 | Hidden (of 29, new policy) | Prompts | Contradictions settled | Minutes |
| --- | --- | --- | --- | --- |
| M: memory of day 1 kept | 29, 28, 29 | 53, 51, 43 | 5, 5, 2 | 15.2, 13.4, 13.6 |
| F: no memory | 29, 29, 29 | 24, 67, 45 | 0 | 6.9, 17.9, 11.0 |

- **Day 1:** 25 of 27 on the old policy, 27 prompts, 15 rulings kept.

## Setup

- **Day 1:** one live flight with the old policy; the owner merged the branch; Hive's state was kept.
- **Day 2:** the new policy: the full-refund window 7 days, a 100-rupee minimum, a point per 50 rupees. He asked: "Some of my shop's rules have changed. Update refunds and loyalty points…". Three flights per arm on the merged repo.
- **The hidden suite:** 29 cases from the new policy (12 of them differ from the old).
- Predictions pushed before the flights (`3f7e29b`).
- **Disclosed:** the flights ran on the code shipped by then (`767d66d`: 6 spot checks and the interface check before every delivery, rather than Gate 90's flow named in the predictions). Both arms used the same code.
- The analysis's "rulings kept" read None, because of a glob bug in the driver. The count, 15, was read from the kept file by hand.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| D1 | F's median ≥ 26 of 29 | **Held:** 29 |
| D2 | M's median ≤ F's − 5 (memory makes drift sticky) | **Failed:** 29 vs 29 (memory is safe) |
| D3 | M asks fewer prompts than F | **Failed:** 51 vs 45 |

## What it means

1. **Under a stated change, Hive's memory is safe.** Its contradiction check, built after Gate 38, does the job a drifting owner needs: it asks once, and his latest word replaces the old ruling.
2. **Memory does not save the owner time here.** Each changed rule costs a "which holds now?" question.
3. **Untested:** drift the owner does not announce, where he answers differently without saying his rules changed. Gate 38's real founder drifted that way: 2 of 11 rules held.

## Files

`prompts/`, `referee/` (`flight92.py`, `analyze.py`).

`results/day1/`, `results/day2_M1` to `results/day2_F3`:
- the terminal, prompts and replies;
- scores;
- the run log.
