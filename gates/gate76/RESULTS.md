# Gate 76 results: flight tests of hive start as shipped after Gates 66–75, Nov 1 2026

**Question** (the user, away for a day: "whatever is necessary"). Five changes shipped since the last flight:
- builders ask first;
- overnight questions for the morning;
- a 90-s ask;
- one answer for a repeated question;
- the business-builder split.

Do they fly together through the real `hive start`?

**Answer.**
- **Yes. Both flights flew cleanly, and all six predictions held.**

| Flight | Goal to branch | Hidden acceptance tests | Owner prompts | Builders' cost |
| --- | --- | --- | --- | --- |
| **Live:** `hive start`, owner at the keyboard | 6.0 min | **27 of 27** | 26 | $0.38 |
| **Overnight:** `hive start --overnight`, then `hive morning` | 3.3 min | 15 of 27 at night → **22 of 27** after the morning | 16 | $0.80 |

- **Live, step by step:**
  1. Hive asked "fast or cheap?" once.
  2. The law put 3 builders on the 3-part job.
  3. The interview confirmed 11 rules.
  4. **The split engaged.** The last builder (w3) had the business role and the others "build the rest". All 4 live questions came from w3.
  5. After the build, Hive said "They asked you 4 questions while building, and your answers are built in" and skipped the long review (Gate 68).
- **Overnight, step by step:**
  1. The night builders recorded 16 questions without waiting.
  2. Hive said "They wrote down 16 questions only you can answer… type `hive morning`".
  3. In the morning, `hive morning` asked them one at a time, and the fix round built the answers in. The branch went from 15 to 22 of 27.
- **The 5 overnight misses** were the changed-mind refund windows (full within 14 days, half to 30; 4 tests) and one points case. No night builder asked about them.
  - The live build covered them through the interview, which an overnight build skips because the owner is away.
  - Splitting the night builders too, so one builder records the owner's questions systematically, is a candidate fix; it is untested.

## Setup

- Gate 54's Tiny Shop and three-part goal; its private policy and 27 hidden acceptance tests (`private/g54`), scored in Gate 54 and reused.
- The synthetic owner (Gate 54's brief) answered every prompt and keyboard read.
- `~/.hive` started empty for each flight.
- Driver `referee/flight76.py` (Gate 52's). Predictions pushed before the flights (`1494473`).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| F1 | Live: no crash, one branch | **Held** |
| F2 | Live: the split engages and only the business builder asks | **Held:** w3 asked all 4 |
| F3 | Live: ≥ 24 of 27 | **Held:** 27 |
| F4 | Live: ≤ 45 owner prompts | **Held:** 26 |
| F5 | Overnight: no crash, ≥ 5 recorded, the morning fix runs | **Held:** 16 recorded, fix ran |
| F6 | Overnight: ≥ 22 of 27 after the morning | **Held:** 22 (at the line) |

## What it means

1. **The shipped flow works end to end.** No product fault was found this time (Gates 52 and 54 each found one).
2. **Overnight is the weaker path:** 22 of 27, against 27 of 27 live. It has no interview, and its questions come from whichever builder thinks to ask. The next candidate is to split the night builders too (one builder records the owner's questions for every part, systematically), then test it.

## Files

`prompts/` (owner brief, predictions), `referee/` (`flight76.py`, `analyze.py`).

`results/live/`, `results/overnight/`:
- the owner's whole terminal (`terminal.txt`);
- every prompt and reply (`owner_log.json`);
- scores (`flight.json`);
- run logs.
