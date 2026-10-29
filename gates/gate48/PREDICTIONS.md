# Gate 48 predictions: a fast local reader for Jarvis

Registered Oct 29 2026, before any arm runs. Asked for by the user: can Jev (TypeSafe AI's decision model) help Hive?

## Why this test

Every message the owner sends, Jarvis first works out what he means. It picks one of 9 intents: build, stop the build, a change of mind, a new rule, status, greeting, move to the cloud, shut the cloud down, or anything else. Today that is one Claude Code call of about 5 to 7 seconds before Jarvis can even start answering.

Jev is a "decision model": it picks among options in a fraction of a second. Its open, Apache-2.0 copy **Laya** runs on a laptop CPU and has a multilingual checkpoint, so the owner's messages never leave his machine. Independent tests put these models about 11 points behind the best LLMs, and weaker outside English. The owner writes in English and Hindi-English, with typos. Nobody has measured that, so we do.

## Setup

- **Set:** `set.jsonl`, 120 short messages in the owner's style, each labelled with the intent Jarvis should act on.
  - Languages: 78 English, 42 Hindi or mixed.
  - Intents: 29 anything else, 23 build, 17 status, 14 rule, 9 each for greeting, stop and change of mind, 5 each for cloud on and cloud off.
  - About 10 need the conversation before them, for example "yes" after "Shall I build this?".
  - Written before any arm ran, by the session, with mock product details. They are committed with these predictions; no arm can read the repository.
  - Limitation: the labeller is a Claude model, which may favour the Claude arm.
- **Arms** (`referee/run48.py`):
  - **claude:** Hive's reader today (`assistant.CLASSIFY` through `explain.ask_json`), in the lab container.
  - **laya-ml** and **laya-en:** Laya 0.4.17, multilingual and English checkpoints, on 2 CPUs (a separate container, `--cpus 2`).
    - The question is one `choice` over the 9 intents, each described by Jarvis's own definitions.
    - The state is the conversation plus the newest message.
    - The model is loaded once and warmed up, as Jarvis would keep it.
- **Hybrid** (what would ship): Laya's answer when its confidence is at least t, otherwise Claude's.
  - t is fitted on the odd ids only: the lowest t at which Laya's accepted answers there are at least 95% right.
  - It is scored on the even ids.
- **Analysis:** `referee/analyze48.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| L1 | Claude reads at least 90% of the messages right | 75% |
| L2 | Laya-ml reads at least 80% right | 40% |
| L3 | Laya-ml's median time is 1 second or less on 2 CPUs | 60% |
| L4 | On the test half the hybrid is within 3 points of Claude, with Laya answering at least half the messages | 35% |
| L5 | Laya-ml is at least 10 points worse on Hindi or mixed messages than on English | 55% |
| L6 | Laya-ml never calls stop, cloud on or cloud off for a message meaning something else | 45% |

## Decision rules

- **Ship:** L4 holds. Jarvis reads with Laya first, when Laya is installed, and asks Claude only when Laya is unsure. It stays optional, so Hive works without it.
- **Kill:** on the test half the hybrid loses more than 3 points, or Laya answers fewer than 30% of messages. Claude stays the only reader, and BRAIN records why.
- **Either way,** a wrong stop costs most. Today Jarvis stops a running build on the first reading with no confirmation, while the cloud actions already ask. If Laya ships, a stop it reads must be confirmed with a tap.

## Cost

About 120 Claude calls (around $1) and a few minutes of CPU. Laya and its models are free.

## Amendment (Oct 29 2026, after the registered arms ran, before v3 runs on this set)

The registered arms are scored (kill fired: Laya-ml 42.5%, Claude 92.5%). Two causes were then found on the separate practice set `dev.jsonl` (48 new messages, never in this set):
- **Speed:** PyTorch used all 24 host threads inside a 2-CPU container. With `OMP_NUM_THREADS=2` the median fell from 5.0 to 0.55–0.72 s.
- **Accuracy:** the catch-all "anything else" was almost never chosen. Splitting it into concrete meanings and tightening "stop" (v3) raised practice accuracy from 18/48 to 30/48, and wrong stops from 7 to 1. Yes/no questions per meaning (v4: 16/48) and the English checkpoint with v3 (29/48) did worse. Claude read 46/48 of the practice set.
- On the practice set no variant reaches 95% at any confidence threshold (v3 at ≥ 0.9: 9 of 11), so the registered hybrid rule would never let Laya answer.

**Run once on this set:** laya-ml with v3, 2 threads (`run48.py laya-ml <out> --variant v3`).

| # | Prediction | Odds |
| --- | --- | --- |
| A1 | v3 reads 55% to 72% of the 120 right | 60% |
| A2 | Median time ≤ 1.0 s (L3 under the fixed setting) | 85% |
| A3 | v3 makes at most 3 wrong stop calls (v1: 13) | 55% |
| A4 | The hybrid rule (threshold fitted on the practice set) still lets Laya answer nothing, so Claude stays the only reader | 85% |
