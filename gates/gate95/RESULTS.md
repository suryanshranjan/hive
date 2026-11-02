# Gate 95 results: show the ordinary case first, Nov 2 2026

**Question.** Gate 93's baseline fails pass^5: one flight in five ships a subtle error (an unsafe new default, a changed result form, state carried between calls) that only an ordinary case would expose, and the spot checks never led with one. If every part's first spot check is its most ordinary case, does that close the gap?

**Answer.**
- **All five flights succeeded: pass^5 held for the first time in any gate.** pass^1 1.00, median hidden 27, median prompts 31. The claim fired.
- **The mechanism did what it was told.** In the four flights where the review ran, the first check was the plain case: "Asha returns a 1,000-rupee order … paid by card, 5 days after delivery, because she changed her mind: she gets 1,000 rupees". Gate 93's live1 had opened with a cancelled order marked damaged.
- **Honest limit:** five of five against Gate 93's four of five is one flight's difference. It is as likely to be luck as the change. pass^5 must hold again before anyone relies on it.

| Flights | Hidden | Prompts | pass^1 | pass^5 |
| --- | --- | --- | --- | --- |
| Gate 93 (baseline) | 19, 25, 27, 27, 27 | median 33 | 0.80 | no |
| **Gate 95 (ordinary case first)** | 27, 26, 25, 27, 27 | median **31** | **1.00** | **yes** |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| C1 | pass^1 ≥ 0.8 | **Held:** 1.00 |
| C2 | pass^5 | **Held** |
| C3 | Median prompts ≤ 38 | **Held:** 31 |
| C4 | No delivery breaks a stated interface | **Held** |
| Claim | C2 and C3 | **Fired** |

## What changes in Hive

- **The ordinary case first stays** (merged as `504554f`), with the interface check's narrowing from Gate 94.
- **Where Hive stands now, Tiny Shop with a synthetic owner:**
  - 5 of 5 flights right;
  - about 31 prompts and 9–14 minutes per feature;
  - Hive's own spend still 5–8× the builders' (Gap 3 open).
- **Next:** repeat the five flights to see whether pass^5 holds, then the open gaps.
  - Hive's own spend: the default model only where answers become rules.
  - A harder real-codebase sample.
  - The interview's 12–17 prompts.
  - The founder.

## Files

`prompts/`, `referee/` (`flight95.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
