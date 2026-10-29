# Gate 49 results: the fast reader, trained on the owner's style, Oct 30 2026

**Question** (after Gate 48, "never give up"): Laya, the open copy of Jev, read only 42.5% of the owner's messages untrained. Trained on examples of his style, can it take a share of Jarvis's reading off Claude without losing accuracy?

**Answer.**
- **Yes. Ship fired.**
  - Trained on 444 owner-style messages, Laya read **77.5%** of Gate 48's 120 held-out messages right (untrained: 42.5%).
  - Hindi or mixed messages: 73.8% (untrained: 33.3%).
  - Median time: **0.55 s** on 2 threads, against about 4.2 s for a Claude call.
- **The hybrid beats Claude alone.** Laya answers when its confidence is 0.5 or more (a threshold fitted on the separate practice set); otherwise Claude answers.
  - Laya answered 56% of messages.
  - The hybrid read **94.2%** right, against Claude's 92.5%.
  - Of the 67 messages Laya answered, 61 were right (91%).
- **The disclosed leak did not drive it.** On the 80 exam messages that share no 3-word phrase with the training set, the trained model read 73.8% right.
- **Two risky misreads got past the threshold, and both are already guarded:**
  - "don't build anything today" was read as a stop. A stop that was not said plainly is confirmed with a tap (since Gate 48).
  - "cloud machine chalu hai kya?" was read as a move to the cloud. Cloud actions always ask first.
- **Not a full replacement.** Alone, the trained model is still 15 points behind Claude, and it knows only Gate 48's 9 meanings, not the builder commands added since.

| Reader | Exam accuracy | Hindi / mixed | Median time | Share it answers |
| --- | --- | --- | --- | --- |
| Claude (Gate 48) | 92.5% | 92.9% | about 4.2 s | 100% |
| Laya untrained (Gate 48) | 42.5% | 33.3% | 0.68 s | 0% under the hand-off rule |
| **Laya trained** | **77.5%** | 73.8% | **0.55 s** | — |
| **Hybrid** (trained Laya at confidence ≥ 0.5, else Claude) | **94.2%** | — | 0.55 s for 56% of messages | 56% Laya |

## Predictions scored (registered code: `referee/analyze49.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| T1 | At least 75% right | **Held:** 77.5% |
| T2 | At least 85% right | **Failed:** 77.5% |
| T3 | Hindi or mixed at least 65% | **Held:** 73.8% |
| T4 | Median at most 1.0 s on 2 threads | **Held:** 0.55 s |
| T5 | At most 3 wrong stop or cloud calls | **Failed:** 7. Five fell below the threshold, so Claude answered them; the two that passed are confirmed with a tap |
| T6 | Hybrid within 3 points of Claude, with Laya answering at least 50% | **Held:** 94.2% vs 92.5%, 56% |
| Ship | T6 | **Fired** |
| Kill | | **Did not fire** |

## Deviations (disclosed)

- **Memory:** the first training run was killed for lack of memory (6 GB container).
  - The rerun used `micro_batch=4, grad_accum=16` instead of the defaults `8, 8`. The effective batch is the same, 64.
  - The container got 9 GB.
  - Neither change was in the registration.
- **Training items:** the trainer held back 44 of the 444 rows for its own calibration and evaluation, so it trained on 400.
- **The leak** registered before training: exact copies of exam messages were removed, and the clean-subset score is reported above.

## What changes in Hive

`hive/fastread.py`: Jarvis reads with the trained model first, when Laya and a trained reader are installed (`HIVE_FAST_READER` or `~/.hive/reader`). It decides alone only:
- at confidence 0.5 or more;
- for meanings that need no further details: greeting, status, chat, stop and cloud (both confirmed with a tap).

Everything else goes to Claude:
- what to build, a new rule, or a change of mind;
- questions, which may need the code read;
- any message naming a builder or an agent ("stop w2", "use 2 Codex");
- while a build runs, anything but greetings and status. The reader was trained before the builder commands existed, so it can only map "stop w2" onto one of its 9 meanings, most likely stopping everything (not tested).

**Next:** retrain with the builder commands (team, instructions mid-build, stopping one builder), so it can take more of the reading.

## Files

- `train.jsonl` (444 messages);
- `referee/run49.py` (rows, train, read), `referee/analyze49.py`;
- `results/` (exam and practice answers with confidence and time, the training log, the analysis).
