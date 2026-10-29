# Gate 49 predictions: train the fast reader on the owner's style

Registered Oct 29 2026, before any training. It follows Gate 48 (asked for by the user: "never give up").

## Why this test

In Gate 48, Laya (the open copy of Jev) read 42.5–45.0% of 120 owner-style messages right against Claude's 92.5%. It was fast (0.68 s on 2 threads) but untrained. Tuning the question on a practice set did not carry over to the exam, and its confidence was too poorly calibrated for a hand-off. The obvious next step is what Laya ships for: fine-tuning on labelled examples of the owner's own messages.

## Setup

- **Training set:** `train.jsonl`, 444 owner-style messages labelled with the same 9 intents (reply 109, build 87, rule 55, status 51, change 40, stop 33, cloud off 25, greeting 22, cloud on 22).
  - A separate agent wrote 480 of them without reading Gate 48's sets.
  - 36 rows matched a Gate 48 exam or practice message exactly (case and punctuation aside) and were removed before training.
  - **Disclosed leak:** the brief to that agent named some hard cases word for word, and several of those were exam messages ("stop sending me so many messages", "status page for creators bana do", "no, for brands too", "haan kar do"). Their exact copies are removed, but close variants may remain. Accuracy is also reported on the exam messages that share no 3-word sequence with any training message.
  - It is committed with these predictions.
- **Training:** Laya 0.4.17's own `finetune` on the multilingual checkpoint, 4 epochs, option-order shuffling, CPU (`referee/run49.py train`).
  - The question is Gate 48's registered v1 (Jarvis's 9 definitions), and the state is the conversation plus the newest message.
- **Exam:** Gate 48's 120 messages (`gates/gate48/set.jsonl`), unchanged. They were never trained on.
- **Hand-off threshold:** fitted on Gate 48's practice set (`gates/gate48/dev.jsonl`, 48 messages, also never trained on) as the lowest confidence at which the trained model's accepted answers are at least 95% right (with at least 5 accepted).
  - Hybrid: the trained model's answer when its confidence is at or above the threshold, otherwise Claude's (Gate 48's recorded answers).
- **Analysis:** `referee/analyze49.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| T1 | The trained model reads at least 75% of the 120 right (untrained: 42.5%) | 55% |
| T2 | It reads at least 85% right | 25% |
| T3 | Hindi or mixed messages: at least 65% right (untrained: 33.3%) | 50% |
| T4 | Median time per message stays at or under 1.0 s on 2 threads | 85% |
| T5 | At most 3 wrong stop or cloud calls (untrained: 26) | 50% |
| T6 | The hybrid is within 3 points of Claude (92.5%) with the trained model answering at least 50% of messages | 30% |

## Decision rules

- **Ship:** T6 holds. Jarvis reads with the trained model first (optional, when Laya is installed) and asks Claude only below the threshold. Stop and cloud actions keep their confirmations.
- **Kill:** the trained model answers fewer than 30% of messages at the threshold, or the hybrid loses more than 3 points. Claude stays the only reader. The finding is recorded with how far training moved it.

## Cost

Free: CPU training in the lab container, and Claude's answers are reused from Gate 48.
