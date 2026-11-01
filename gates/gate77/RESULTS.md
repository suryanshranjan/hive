# Gate 77 results: split the night builders too? Nov 1 2026

**Question.** Gate 76's overnight flight scored 22 of 27 after `hive morning`. Would giving the owner's decisions to one night builder, who records his questions systematically (Gate 74's split, recording rather than asking), raise that, without flooding his morning?

**Answer.**
- **No measurable gain. The claim did not fire, and nothing ships.** The split worked as designed, but scored only 0.7 of a test higher.

| Means over 3 flights | Hidden at night | Hidden after the morning | Questions recorded (morning load) | Night build | Builders' cost |
| --- | --- | --- | --- | --- | --- |
| Control (as shipped) | 14.0 of 27 | **25.0** (26, 24, 25) | 12.0 (16, 15, 5) | 3.2 min | $0.78 |
| Split night builders | 12.3 of 27 | **25.7** (26, 26, 25) | 15.3 (19, 17, 10) | 3.3 min | $0.82 |

- **The split worked as designed:** in all three split flights only the business builder (w3) recorded questions.
- **Gate 76's 22 was mostly a low draw.** Three more as-shipped overnight flights scored 26, 24 and 25. The overnight path is about 25 of 27 after the morning, not 22.
- **Little room is left.** One changed-mind refund case was missed in all six flights. Beyond that, the control missed 0, 2 and 1 more tests per flight, and the split 0, 0 and 1. A +2 gain (N1) would have needed near-perfect flights.
- **The split's night build scored lower (12.3 vs 14.0).** Its business builder records first and builds guesses after, so less is right before the morning. The morning answers more than make up for it.
- **The morning load rose 28%** (15.3 vs 12.0 questions), within N3's bound.

## Setup

- **The job, owner and score:** Gate 76's. Tiny Shop's three-part goal; the private policy and 27 hidden tests in `private/g54`; the synthetic owner (Gate 54's brief) answered every prompt, including each morning question.
- **Each flight:** `hive start --overnight`, then `hive morning`, from an empty `~/.hive`. The law put 3 builders on every flight.
- **Arms:**
  - **control:** as shipped;
  - **split:** `HIVE_SPLIT_OVERNIGHT=1`.
- **Order:** control1, split1, control2, split2, control3, split3, one at a time.
- Predictions pushed before the flights (`3bb1525`).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| N1 | Split's mean after the morning ≥ control's + 2 | **Failed:** +0.7 (25.7 vs 25.0) |
| N2 | The split engages and only the business builder records | **Held** in all 3 |
| N3 | Split's questions ≤ 1.5× control's | **Held:** 1.28× |
| N4 | No crash; the morning fix runs in all six | **Held** |
| Claim | N1 and N3 | **Did not fire** |

## What changes in Hive

- **Nothing ships.** The overnight split stays behind `HIVE_SPLIT_OVERNIGHT=1`, off by default. It is tested, and showed no gain worth a heavier morning.
- **The overnight path is better than Gate 76 showed:** 25.0 of 27 after the morning, over three flights.
- **Next candidate** (the registered rule for a failed N1): a short interview before the owner leaves. He is at the keyboard when he types `hive start --overnight`.
  - The live flight, which has the interview, scored 27 of 27, but that is one flight.
  - At most about 2 tests of 27 are left to gain, so this is low priority.

## Limits

- Three flights per arm, on one small project, with a synthetic owner whose answers never drift. The hidden tests were written in Gate 54 and are reused.
- Builders cost $4.8 in all; the synthetic owner $4.8.

## Files

`prompts/` (owner brief, predictions), `referee/` (`flight77.py`, `analyze.py`).

`results/<arm><k>/`, for each of the six flights:
- the owner's whole terminal (`terminal.txt`);
- every prompt and reply (`owner_log.json`);
- the questions recorded overnight (`questions.json`);
- scores (`flight.json`);
- the run log.
