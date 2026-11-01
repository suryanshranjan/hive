# Gate 87 predictions: Hive's own reading steps on a small model (Gap 3)

Registered Nov 2 2026, before the flights.

## Why this test

- **Gate 85:** Hive's own model spend was 4.8–8.6× the builders'.
- **Where it goes:** 45% to interpreting the interview's answers (`settled_by`, `_amend`, `_rule`), 19% to reading the owner's free-text replies (`understand`), and 22% to the spot checks. All of these go through `hive/explain.py`'s one model command, the CLI's default model.
- **These are short reading tasks.** Gates 62, 64 and 65 found bigger models helped no *builder* role. No gate has tested a smaller model for Hive's own steps.

## Setup

- **Gate 85's five live flights, unchanged except one setting:** `HIVE_EXPLAIN_CMD='claude -p --output-format json --model claude-haiku-5-5'`.
  - This covers every call through `explain.py`: interview, replies, rule sheet, and the spot checks' apply and recheck.
  - The code sheet's and the spot checks' code-reading agents keep their own commands, about 5% of spend.
- **Same project, private policy, 27 hidden tests and synthetic owner.**
- Driver `referee/flight87.py` (Gate 85's, plus the setting), analysis `referee/analyze.py` (compares with Gate 85), committed now.
- **Order:** after Gate 86's Hive arm finishes, since both need `~/.hive`.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| H1 | Hive's own spend, mean over flights, ≤ 0.4× Gate 85's | 70% |
| H2 | pass^1 ≥ 0.8 (no drop) | 60% |
| H3 | Median hidden ≥ 26 of 27 | 65% |
| H4 | Median owner prompts ≤ 1.2× Gate 85's (the cheaper reader does not make him repeat himself) | 70% |

## Decision rules

- **Claim (H1, H2 and H3):** Hive's own reading steps run on the small model by default.
- **H1 holds but H2 or H3 fails:** find the step that lost quality (spend by step, and the transcripts), and keep the default model for that step only.

## Limits

- Five flights against five, on one small project, with a synthetic owner.
- About $15.
