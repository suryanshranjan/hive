# Gate 48 results: a fast local reader for Jarvis (Laya, the open copy of Jev), Oct 29 2026

**Question** (from the user): can Jev, TypeSafe AI's decision model, help Hive? Concretely: can its open, Apache-2.0 copy Laya, running on the owner's own machine, read what his Telegram messages mean as well as Claude, and much faster?

**Answer.**
- **Not as it ships. Kill fired: Claude stays the only reader.**
  - On 120 messages in the owner's style (65% English, 35% Hindi or mixed), Claude read 92.5% right.
  - Laya's multilingual checkpoint read 42.5% right, and the English one 45.0%. Both were far worse on Hindi and mixed messages: 33% and 31%.
  - Laya called "stop the build" or a cloud action wrongly on 26 messages.
- **Speed is real once it is set up right.** With PyTorch held to the container's 2 CPUs, Laya answered in a median 0.68 s against Claude's 4.2 s. Untuned, it used all 24 host threads inside 2 CPUs and took 5 s.
- **Tuning the question did not carry over.**
  - On a separate practice set of 48 new messages, splitting "anything else" into concrete meanings and tightening "stop" (v3) raised accuracy from 38% to 63%.
  - On the 120 it gave 45.0%, against v1's 42.5%: the gain was fitted to the practice wording.
  - Its confidence is poorly calibrated: even at 0.9 or above, v3 was right on 9 of 11 practice messages. So the registered hybrid (Laya when confident, Claude otherwise) never lets Laya answer.
- **Found on the way, now fixed in Hive.** Claude itself read "don't build anything today" as *stop the build*, and Jarvis stopped builds on its first reading with no confirmation. Jarvis now asks before stopping unless he plainly said to stop. "Keep going" keeps the build.

| Reader | Accuracy | English | Hindi / mixed | Median time | Wrong stop or cloud calls |
| --- | --- | --- | --- | --- | --- |
| Claude (Hive today) | **92.5%** | 92.3% | 92.9% | 4.2 s | 1 ("don't build anything today") |
| Laya multilingual, v1 (registered) | 42.5% | 47.4% | 33.3% | 5.0 s (24 threads on 2 CPUs) | 26 |
| Laya English, v1 (registered) | 45.0% | 52.6% | 31.0% | 8.6 s (same) | – |
| Laya multilingual, v3 (amendment) | 45.0% | 47.4% | 40.5% | **0.68 s** (2 threads) | 5 wrong stops |

## Predictions scored

Registered: `referee/analyze48.py`, output in `results/analysis.txt`.

| # | Prediction | Result |
| --- | --- | --- |
| L1 | Claude ≥ 90% | **Held:** 92.5% |
| L2 | Laya-ml ≥ 80% | **Failed:** 42.5% |
| L3 | Laya-ml median ≤ 1.0 s on 2 CPUs | **Failed** as registered (5.0 s, a thread misconfiguration); 0.68 s once fixed (A2) |
| L4 | Hybrid within 3 points of Claude with Laya answering ≥ 50% | **Failed:** no threshold met 95% on the dev half, so Laya answered 0% |
| L5 | Laya-ml ≥ 10 points worse on Hindi or mixed | **Held:** 47.4% vs 33.3% |
| L6 | Laya-ml never calls stop or cloud wrongly | **Failed:** 26 such calls |
| Ship | L4 | **Did not fire** |
| Kill | | **Fired** |

The amendment was registered after the arms above and before v3 ran on this set (`PREDICTIONS.md`):

| # | Prediction | Result |
| --- | --- | --- |
| A1 | v3 reads 55–72% right | **Failed:** 45.0% |
| A2 | Median ≤ 1.0 s with 2 threads | **Held:** 0.68 s |
| A3 | At most 3 wrong stop calls | **Failed:** 5 |
| A4 | The hybrid still lets Laya answer nothing | **Held** |

## What it means for Hive

1. **A decision model out of the box does not read a founder's texting.** These messages are short, often Hindi-English, often depend on the conversation, and mostly fall in "anything else". That is where these models are weakest, as the vendor's own docs warn about catch-all options.
2. **The speed is there (0.7 s), so the open question is training.** Laya ships a trainer, and a few hundred labelled messages in the owner's style might close the gap. That is the next experiment (in `lab/QUEUE.md`). Any training set must be written separately from these 120, which stay the exam.
3. **Jarvis's own reading has a cheap fast path already** (greetings, "status"); this gate adds nothing to it.

## Setup and limits

- **Set:** `set.jsonl`, 120 messages labelled before any arm ran. The labeller was a Claude model, which may favour the Claude arm.
- **Practice set:** `dev.jsonl`, 48 messages.
- **Laya:** 0.4.17 from PyPI, in a separate `python:3.12-slim` container with `--cpus 2`.
- **Claude:** Claude Code 2.1.311, run through Hive's own reader.
- **Limits:** one labeller and one owner's style; Laya was not fine-tuned.

## Files

- `set.jsonl`, `dev.jsonl`;
- `referee/run48.py` (arms and variants), `referee/analyze48.py`;
- `results/` (every arm's answers with confidence and time, on both sets; the registered analysis).
