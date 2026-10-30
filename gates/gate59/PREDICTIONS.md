# Gate 59 predictions: the fast reader, retrained with the builder commands

Registered Oct 31 2026, before any training. Asked for by the user ("do the remaining gaps").

## Why this test

Gate 49's trained reader (Laya, the open copy of Jev) took 56% of Jarvis's reading at 0.55 s, but it knows only Gate 48's 9 meanings. Since then Jarvis gained the builder commands: who is doing what, choosing the team, stopping one builder, and instructions mid-build. So Hive keeps the reader off any message naming a builder or an agent, and during a build off everything but greetings and status. That is where the founder steers most. Retrained on all 13 meanings, can it take a share of that reading without losing accuracy?

## Setup

- **Training set:** written by a separate agent that read no exam, with all 13 meanings (team, set_team, stop_builder and instruct included) in the founder's style. 560 written.
  - 14 matched an exam message exactly and were removed: short common messages such as "hi", "ok", "stop w2", "kitna hua". The exam keeps them.
  - 58 held back, stratified by meaning, as the practice set for fitting the hand-off threshold (`practice.jsonl`).
  - **488 to train on** (`train.jsonl`).
  - All three files are committed now.
- **Exam:** `exam.jsonl`, 130 messages, written by a second, separate agent that read no file in the repository, about 48% Hindi or mixed. Mix: reply 25, build 14, instruct 12, 10 each for status, rule, team, set_team and stop_builder, 7 each for change and stop_build, 5 each for greeting, cloud on and cloud off. Never trained on; committed now.
- **Arms:**
  - **Trained:** Laya 0.4.17's `finetune` on the multilingual checkpoint, Gate 49's settings (4 epochs, option shuffling, micro-batch 4 × 16). The question has 13 options, Jarvis's own definitions (`hive/assistant.py` `INTENTS_V2`). Read on 2 threads.
  - **Claude:** Hive's reader today (`assistant.CLASSIFY`, which already knows the 13 meanings).
- **Hybrid:** the trained answer at confidence ≥ the practice-fitted threshold, otherwise Claude's.
- **Analysis:** `referee/analyze59.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| B1 | The trained model reads ≥ 75% of the exam right (Gate 49: 77.5% on 9 meanings) | 50% |
| B2 | It reads ≥ 70% of the builder commands right (team, set_team, stop_builder, instruct) | 50% |
| B3 | Claude reads ≥ 88% of the exam right | 70% |
| B4 | Median time ≤ 1.0 s on 2 threads | 85% |
| B5 | No confident wrong stop (whole build or one builder) or cloud call | 45% |
| B6 | The hybrid is within 3 points of Claude, with the trained model answering ≥ 50% | 40% |

## Decision rules

- **Ship:** B6 holds. Hive replaces its crude keyword veto with the retrained reader: messages it reads as a builder command go to Claude (which fills in the builder, the team or the instruction), and greetings, status, chat and "who's doing what" are answered fast, during builds too. Stop and cloud actions keep their taps.
- **Kill:** the trained model answers fewer than 30% at the threshold, or the hybrid loses more than 3 points. Gate 49's reader stays as it is, behind the keyword veto.

## Cost

CPU training in the lab (about 25 minutes) and about 130 Claude calls (about $1).
