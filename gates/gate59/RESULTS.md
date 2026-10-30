# Gate 59 results: the fast reader, retrained with the builder commands, Oct 31 2026

**Question** (from the user: "do the remaining gaps"). Gate 49's trained reader (Laya, the open copy of Jev) knows 9 meanings, so Hive keeps it off builder commands. Retrained on all 13, can it take a share of that reading too?

**Answer.**
- **No. Kill fired.**
  - On a new 130-message exam written by an independent agent, the retrained reader got **58.5%** right, against Claude's **95.4%**.
  - On the four builder commands it got 40.5% (Claude 92.9%). Hindi or mixed messages: 46.0%.
  - Its confidence was well calibrated: at the practice-fitted threshold (0.7) it made no wrong stop or cloud call. But it answered only 22% of messages, and the hybrid scored 93.8%, 1.6 points under Claude alone.
- **The builder commands blur into each other and into their neighbours.** "stop w2" was read as stopping everything; "w2 kya kar raha hai" as chat; "add a csv download too" as a new build; "put w3 on codex" as a build. With 440 training items for 13 meanings, about 35 per meaning, these fine distinctions were not learned.
- **Gate 49's reader still holds** (post hoc, not registered). Gate 49 was scored on an exam the session wrote itself, so a style match was possible. Run on this independent exam's 88 messages with its 9 meanings, Gate 49's shipped reader got **80.7%** right. At its shipped threshold (0.5) it answered 55% and was right on 45 of 48 (94%). Its one risky slip was "cloud_off" read as "cloud_on", and cloud moves always ask with a tap. So Gate 49 stands: its exam did not flatter it.

| Reader | Exam accuracy | Builder commands | Hindi / mixed | Median | Hand-off |
| --- | --- | --- | --- | --- | --- |
| Claude (Hive today) | **95.4%** | 92.9% | — | about 4 s | — |
| Laya retrained, 13 meanings | 58.5% | 40.5% | 46.0% | 0.67 s | answers 22% at ≥ 0.7; hybrid 93.8% |
| Gate 49's reader, 9 meanings (post hoc, 88 items) | 80.7% | not trained | — | — | answers 55% at ≥ 0.5, 94% right |

## Predictions scored (registered code: `referee/analyze59.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| B1 | Trained ≥ 75% | **Failed:** 58.5% |
| B2 | Builder commands ≥ 70% | **Failed:** 40.5% |
| B3 | Claude ≥ 88% | **Held:** 95.4% |
| B4 | Median ≤ 1.0 s | **Held:** 0.67 s |
| B5 | No confident wrong stop or cloud call | **Held:** none |
| B6 | Hybrid within 3 points of Claude, the reader answering ≥ 50% | **Failed:** 93.8% vs 95.4%, answering 22% |
| Ship / Kill | | **Kill fired** |

## What it means

1. **Hive keeps Gate 49's 9-meaning reader behind its keyword guard.** Builder commands, and during a build anything but greetings and status, go to Claude. That is the current behaviour; nothing changes.
2. **A fast reader for builder commands needs far more examples per meaning,** or the context the command depends on (whether a build is running, who w2 is), which a single classification question does not carry. Not worth more now: Claude reads them at 92.9%.

## Setup

- Training: 560 messages written by one agent, with 14 exact exam matches removed and 58 held back as practice. Laya's own trainer kept 48 more for calibration, leaving 440. Training took 28 minutes on CPU, with Gate 49's settings.
- Exam: 130 messages written by a second agent that read no file in the repository (48% Hindi or mixed).
- Claude: `assistant.CLASSIFY`, run in the lab container.

## Files

- `train.jsonl`, `practice.jsonl`, `exam.jsonl`;
- `referee/run59.py`, `referee/analyze59.py`, `referee/posthoc_g49_reader.py`;
- `results/` (every arm's answers with confidence and time, the training log, the analysis, Gate 49's reader on this exam).
