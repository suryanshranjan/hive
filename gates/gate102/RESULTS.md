# Gate 102 results: the interview before an overnight build, Nov 2 2026

**Question.** In Gate 99 overnight flights succeeded only 3 times in 5: night builders missed decisions nobody asked about. The owner is at the keyboard when he types `hive start --overnight`. If Hive interviews him then, as on the live path, do overnight flights become reliable?

**Answer.**
- **Yes. Every flight was right:** five of five scored 27 of 27 after the morning. That is pass^5, against pass^1 0.60 and a median of 25 in Gate 99.
- **The builds were already right at night** (27, 27, 27, 26, 27), before the morning answers.
- **The owner's time:** a median of 30 prompts in all, split as about 11 interview questions, 9 rule confirmations, and about 10 in the morning. In Gate 99 it was 14, all in the morning. He spends about 16 more prompts before he leaves and saves the morning's failures.
- **Cost:** $1.53 a feature, against $1.09. N4's limit of $1.50 narrowly failed: more builders' work at night ($0.77–1.21) on a fuller brief.

| Overnight flights | After the morning | At night | Prompts | Cost a feature | Minutes |
| --- | --- | --- | --- | --- | --- |
| Gate 99 (no interview) | 26, 23, 25, 26, 21 (pass^1 0.60) | | median 14 | $1.09 | 3–5 |
| **Gate 102 (interview first)** | **27, 27, 27, 27, 27** | 27, 27, 27, 26, 27 | median **30** | **$1.53** | 6–8 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| N1 | pass^1 ≥ 0.8 | **Held:** 1.00 (pass^5) |
| N2 | Median after the morning ≥ 26 | **Held:** 27 |
| N3 | Median prompts ≤ 35 | **Held:** 30 |
| N4 | Mean cost ≤ $1.50 | **Failed:** $1.53 |

## What changes in Hive

- **The interview before an overnight build ships.** It is already on main (merged as `66210da` before the test). By the registered rule, N1 and N2 held.
- **The overnight path now matches the live one:** 5 of 5 right in both (Gates 95, 96, 98 live; 102 overnight).
- **MAST FM-2.2** (failure to ask for clarification) on the overnight path is closed by asking before the night, not during it.

## Files

`prompts/`, `referee/` (`flight102.py`, `analyze.py`).

`results/overnight1` to `results/overnight5`:
- the terminal, prompts and replies;
- scores and spend;
- the run log.
