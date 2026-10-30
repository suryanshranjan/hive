# Gate 57 results: spot checks for the skimming owner, Oct 30 2026

**Question** (from the user: "Test it"). A skimming owner corrects only what he remembers when he reads rules (Gates 55–56). Does he catch more when Hive shows him concrete outcomes of the built code, one at a time ("Ravi's 100-rupee invoice is paid 31 days late: the late fee comes to 2 rupees. Right?")?

**Answer.**
- **He engaged far more, but the sheet did not get better. Neither the ship rule nor the kill fired.**

| Same skimming owner, same build | Owner corrections | Decisions right after (of 25) | Hidden pass |
| --- | --- | --- | --- |
| Rule list, 81 rules (SL) | 11 replies | **9** | 48.8% |
| Spot checks, 30 outcomes (SP) | **17 of 30 outcomes corrected** | 7 (+4 partly) | 51.2% |
| No owner (N0) | – | – | 33.2% |

SP − SL = +2.4 points (CI −10.0 to +15.6).

- **Concrete outcomes did wake up a skimmer's memory.** He caught details he passes over in a list:
  - "No, 5 days late is still the grace period, so the fee is 0";
  - "round to the nearest 5 cents, so it should be 94.55";
  - "it should still get a label: FY2027-Q1, ignoring the time";
  - "an old value of 0 should give 0.0".
- **Two places lost what he said:**
  1. **Turning corrected cases into rules.** One model call rewrote the sheet from his 17 corrections, and some came out partial or in conflict. The late fee's minimum and cap ended up contradicting each other. The 5-cent rounding was applied only to discounted totals. Case answers lose detail on the way to rules, as in Gate 41.
  2. **Coverage.** 30 cases touched 9 of the 10 functions, but not every decision. Some functions' key choices never came up as a case: trimming the highest and lowest rating, "untitled" for an empty slug, phone numbers returned unchanged.
- **The two reviews caught different decisions** (post hoc, not registered):
  - the list fixed 5 that the spot checks missed: the headline rules he remembers, such as platinum at 20,000 and the 500 minimum;
  - the spot checks fixed 3 that the list missed: details such as the grace period, times on dates, and a zero divisor;
  - together, 12 of 25, against 9 for the list alone.

  Conjecture: the list and spot checks are complementary. A combined review, with each corrected case re-run after the fix to confirm, could keep both.

## Setup

- **Rules:** Gate 55's rule set (published; builders never see it), new draws (seeds 57100, 57200000). Predictions pushed before the run (`f0300e4`).
- **Stage 1:** a fresh N0 build. From its code (never the oracle):
  - the describer wrote D (81 rules);
  - a spotter ran the code on 30 concrete cases where it made a non-obvious choice (`prompts/spotter_brief.md`).
- **Two separate sessions with the same skimming owner** (Gate 55's brief and policy prose):
  - **SL:** D as a terminal rule list;
  - **SP:** the 30 cases one at a time, his corrections applied to D by one model call (`prompts/apply_brief.md`).
- **Stage 2:** 3 fresh builders each. A judge labelled every declared decision before stage 2.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| U1 | SP gets ≥ 15 more points of decisions right than SL | **Failed:** −8 points (7 vs 9; SP had 4 more partly right) |
| U2 | Hidden SP ≥ SL + 5 | **Failed:** +2.4 |
| U3 | The skimmer corrects ≥ 25% of spot checks | **Held:** 57% (17 of 30) |
| U4 | Applying his corrections spoils at most 1 right decision | **Held:** 0 |
| Ship / Kill | | **Neither fired** |

## What it means

1. **The lever exists: concrete outcomes get a skimmer's attention.** 17 corrections in 3 minutes, many of them details.
2. **Hive's machinery after the review loses it.** Converting case answers into rules lost detail, and the 30 cases did not cover every decision. Both are fixable without asking more of the owner:
   - after the fix, re-run each corrected case and show it again;
   - draw the cases from every decision the code takes, not the 30 a spotter picks.
3. **Nothing changes in the product yet.** The next wind-tunnel step is the combined review: list first for the headlines, then spot checks on what the list did not change, then each corrected case re-run. That needs no founder time. The founder test follows if it wins.

## Limits

- One run per arm, a synthetic skimmer, one rule set (shared with Gates 55–56).
- The union figure (12 of 25) is post hoc.

## Files

`prompts/` (spotter, apply, owner, judge briefs; predictions), `referee/` (`review57.py`, analysis), `results/`:
- sheet D, the 30 spot checks with the engine's outputs, both reviews' transcripts and resulting sheets;
- judge labels;
- probes, costs and run log.

Also `swarms/`, `logs/`.
