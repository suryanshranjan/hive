# Gate 65 results: an Opus spotter, Oct 30 2026

**Question** (from the user: "Go on", after "a stronger model for Hive's own judgement calls"). The spotter picks the concrete cases the owner checks, and those picks are what found his decisions (Gates 58, 63). Does an Opus spotter pick better cases than the default (Sonnet) one?

**Answer.**
- **Not measurably. Neither the ship nor the kill rule fired.**
- The two spotters wrote about as many cases (96 vs 94), drew about as many corrections (57 vs 56), and left the sheet about as right (32 vs 31 of 50 decisions).

| Same skimming owner, same build (pooled, 50 decisions) | Cases | Corrected | Decisions right | Hidden pass (mean) |
| --- | --- | --- | --- | --- |
| List only (SL) | – | – | 19 | – |
| List, then the Sonnet spotter's cases (CS) | 94 | 56 | 31 | 69.0% |
| List, then the Opus spotter's cases (CO) | 96 | 57 | 32 | 73.0% |

CO − CS = +4.0 hidden points (95% CI −3.4 to +11.6).

- **The hidden gain comes from one run, and is within noise.** Run g60b: +8.0 points (77.6 vs 69.6%); run g60a: 0 (68.4 each).
- **The spotters found different decisions, not more of them.**
  - Opus's cases got 5 decisions right that Sonnet's did not: a slug rule, a bulk-price rule, a rating rule, a card-mask rule and a slug rule on the fresh set.
  - Sonnet's got 4 that Opus's did not: a late-fee rule, the year-end close, the meeting cap and a grade cut-off.
- **Gate 63's hand-over replicated:** spot checks on every part took the skimmer from 19 to 31 of 50 decisions (Gate 63: 18 to 32).
- **Cost:** the Opus spotter cost $0.48–0.53 a build. The Sonnet spotter in Gate 60 cost about $0.23.

## Setup

- From Gate 60's records, for both rule sets: the same N0 build, sheet D, the owner's list review SL, policy and owner brief.
- **CS:** Gate 60's spotter cases (Sonnet). **CO:** a new Opus spotter (`--model opus`), from the same code with the same brief.
- **Both arms:**
  - cases on every function, untouched first (Gate 63's hand-over);
  - a fresh owner session each;
  - each correction applied alone and re-shown.
- One judge per run labelled D, SL, CS, CO and R together.
- 3 builders each, probed on Gate 60's hidden suite.
- Predictions pushed before the run (`6bb9a6d`).
- **Cost:** owner model calls $23.4, builders $3.2, spotters and judges about $1.9.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| K1 | CO ≥ CS + 3 decisions | **Failed:** 32 vs 31 |
| K2 | Hidden CO ≥ CS + 3 | **Held:** +4.0 (CI −3.4 to +11.6; one run carries it) |
| K3 | Opus writes ≤ 1.3× the cases | **Held:** 1.02× |
| K4 | CO spoils ≤ 1 decision SL had right | **Held:** 1 |
| Ship | K1 and K2 | **Did not fire** |
| Kill | CO no better on both | **Did not fire** |

## What it means

1. **No change.** Hive's spotter stays on the default model. A stronger model costs twice as much per build and changes which decisions are found, not how many.
2. **The model is not what limits the spotter.** With either spotter, the skimmer still left 18–19 of 50 decisions not right. What limits it is what a skimmer corrects when shown a case. That points back to the owner: Gate 45 day 2, with the founder.
3. **Across Gates 62, 64 and 65, "a bigger model" did not help at any role tried:** second builder, planner, builders, spotter.

## Limits

- One owner session and one build per arm per rule set, with a synthetic skimmer.

## Files

`prompts/` (judge brief, predictions), `referee/` (`run65.py`, `analyze.py`).

`results/g65a/`, `results/g65b/`:
- both arms' cases, corrections, re-shows, sheets and judge labels (`sheet.json`);
- probes, ask texts, agents and run logs.
