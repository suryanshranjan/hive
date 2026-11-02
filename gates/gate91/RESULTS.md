# Gate 91 results: Hive's own reading on Haiku, on the fixed flow, Nov 2 2026

**Question.** Gate 87 tried Claude Haiku 5.5 for Hive's own reading steps, but a product fault (placeholders) clouded its accuracy. On Gate 90's fixed flow, does Haiku cut Hive's own spend without losing accuracy?

**Answer.**
- **No. The claim did not fire, for the second time.**
- **Haiku cut Hive's own spend to 0.07×** ($0.32 per flight against $4.32), and pass^1 held at 0.80.
- **But the median hidden score fell to 25 again** (Gate 87: 25), against 27 on the default model (Gates 85 and 90).
- **The losses are where the build rests on the interview's rules alone.**
  - In the three flights where builders asked 3 or more questions and the review was skipped, Haiku scored 23, 25 and 24. Its errors were scattered rule details: final-sale double points, the 500-rupee minimum, half refunds, the 50-rupee floor.
  - On the default model, the two flights that skipped the review scored 27 and 27.
  - So Haiku's readings of the owner's answers (`interview._rule`, `settled_by`, `_amend`) lose details that the builders then follow.

| Flights | Hidden | Prompts | Hive's own | pass^1 |
| --- | --- | --- | --- | --- |
| Gate 90 (default model) | 27, 27, 27, 27, 15 | 33, 28, 68, 64, 74 | mean **$4.32** | 0.80 |
| Gate 91 (Haiku 5.5) | 27, 26, 23, 25, 24 | 56, 61, 32, 32, 37 | mean **$0.32** | 0.80 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| H1 | Hive's own spend ≤ 0.4× Gate 90's | **Held:** 0.07× |
| H2 | pass^1 ≥ 0.8 | **Held:** 0.80 |
| H3 | Median hidden ≥ 26 | **Failed:** 25 |
| H4 | Median prompts ≤ 1.2× Gate 90's | **Held:** 37 vs 64 |
| Claim | H1, H2 and H3 | **Did not fire** |

## What changes

- **Haiku does not become the default** for Hive's own steps.
- **Next candidate, by the registered rule:** keep the default model where Hive turns the owner's words into rules (`_rule`, `settled_by`, `_amend`, `apply_one`), and use the small model for the rest. Or try Claude Sonnet 5.5 for all of them, between the two. Either needs its own gate.
- **Hive's own spend stays about 5–9× the builders'** (Gap 3 is open).

## Files

`prompts/`, `referee/` (`flight91.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
