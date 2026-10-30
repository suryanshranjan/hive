# Gate 58 results: the combined review for the skimming owner, Oct 31 2026

**Question** (from the user: "implement the changes and check whatever was the findings"). Gate 57 found that spot checks draw a skimming owner's corrections, but they were lost turning cases into rules, and some functions were never shown. Does the combined review fix that? It runs the owner's rule-list review, then spot checks covering every function the list left as it was, each correction applied on its own and its case shown to him again.

**Answer.**
- **Yes. All four predictions held, and the ship rule fired.**

| Same skimming owner, same build | Decisions right (of 25) | Hidden pass |
| --- | --- | --- |
| No owner (N0) | – | 36.8% |
| Rule list (SL) | 4 (+3 partly) | 43.2% |
| **List, then spot checks with re-show (CB)** | **9** (+4 partly) | **58.8%** |

CB − SL = **+15.6 points** (95% CI +5.2 to +27.6); CB − N0 = +22.0 (CI +13.6 to +31.2).

- **What the spot checks added on top of the list:**
  - 29 cases were shown; 4 functions the list review had changed were skipped.
  - He corrected 10. Every correction was a detail a list hides:
    - "round totals to the nearest 5 cents";
    - "March 27 to 31 is year-end close, not Q4";
    - "the & should become 'and'";
    - "never leave it empty: make it 'untitled'";
    - "show 0% when last month was zero".
  - 6 decisions changed from SL to CB: 5 became right, 1 partly right.
- **Showing the case again caught the conversion loss Gate 57 found.**
  - Of the 10 corrected cases re-shown, he confirmed 9.
  - In the tenth, "don't pad short codes" had been applied as *reject them*. Shown the case again, he said "No, don't reject it, just compute from 1, 2, 3", and the second correction made it right.
- **Nothing he already had right was spoiled** (0 decisions).

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| V1 | CB states ≥ 12 points more decisions right than SL | **Held:** +20 points (9 vs 4 of 25) |
| V2 | Hidden CB ≥ SL + 5 | **Held:** +15.6 |
| V3 | ≥ 80% of re-shown corrections confirmed | **Held:** 90% (9 of 10) |
| V4 | CB spoils at most 1 decision SL had right | **Held:** 0 |
| Ship | V1 and V2 | **Fired** |
| Kill | | **Did not fire** |

## What it means

1. **For an owner who skims, Hive's hand-over should be the list, then concrete cases, then each fix shown back.** The list catches the headlines he remembers, and the cases catch the details he skims past. Showing the fix back catches Hive's own misreadings, which Gate 57 lost.
2. **The remaining gap is still large:** 9 of 25 decisions right, against 25 for a careful owner (Gate 55). Spot checks raise what a skimmer delivers; they do not make him careful. Gate 45 day 2 with the founder is the real test.

## What changes in Hive

`hive/spotcheck.py` is now the hand-over's last step (`hive start`, after the code-sheet review):
- a spotter runs a throwaway copy of the built code on 2 to 5 cases for every part his review left as it was;
- he sees them one at a time, on the phone or in the terminal;
- a question about a case is answered first;
- each correction is applied to that part's rules only, and the case is worked out again from the new rules and shown to him once more;
- a second correction is applied the same way.

`HIVE_SPOTS=0` turns it off.

## Setup

- Gate 55's published rule set, with new draws (seeds 58100, 58200000).
- N0: 3 builders. The describer wrote D (107 rules); the spotter wrote cases for every function.
- Arms:
  - **SL:** the skimming owner reviewed D as a rule list (6 replies, 0.9 min).
  - **CB:** SL's result, then the spot checks.
- Stage 2: 3 fresh builders each.
- Predictions pushed before launch (`13523e0`).
- **A first launch failed before any build:** the lab container's Claude login had expired. It was refreshed and the gate rerun from scratch.

## Limits

- One run per arm, one synthetic skimmer, one rule set (shared with Gates 55–57).
- The synthetic owner's spot-check session cost $4.47 in model calls. A real owner's time is the real cost: 29 cases plus 10 re-shows.
- The re-shown text is long: the worked-out case often restates the whole rule. Shorter re-shows are worth trying.

## Files

`prompts/` (spotter, apply-one, recheck, judge, owner briefs; predictions), `referee/` (`review58.py`, analysis), `results/`:
- sheets D, SL and CB;
- every spot check, correction, re-show and confirmation (`sheet.json`);
- judge labels, probes, costs and run log.

Also `swarms/`.
