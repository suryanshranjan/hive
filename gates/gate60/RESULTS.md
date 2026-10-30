# Gate 60 results: two wings, Oct 30 2026

**Question** (from the user: "Run the tests as required", after the proposal "two wings"). Two independent builds of the same spec should agree wherever the spec is clear and disagree where it leaves a choice open. Does showing a skimming owner only the cases where they disagree (DG) do as well as Gate 58's spot checks (CB), with fewer cases to read?

**Answer.**
- **No. The kill rule fired.**
- **Two builds mostly make the same wrong choices.** Of the probe calls where the first build's result differed from the owner's policy, the second build disagreed on only 19% (47 of 243). Where the spec leaves a choice open, two builds from the same model both pick the natural default, and the owner's rule is usually the one that is *not* natural:
  - a 500-cent minimum order;
  - a year-end close label for 27 to 31 March;
  - platinum from 20,000 points;
  - a 5-day grace period.

  Disagreement finds the detail two builders happen to read differently, not the policy neither could guess.

| Pooled over both runs (50 declared decisions) | Decisions right | Hidden pass (mean) | Cases the owner read |
| --- | --- | --- | --- |
| No owner (N0) | – | 38.2% | – |
| Second build, no owner (B) | – | 34.0% | – |
| Rule list (SL) | 20 | 58.2% | – |
| **List, then spot checks (CB, Gate 58)** | **26** | **63.0%** | 29 |
| List, then disagreement cases (DG) | 20 | 57.0% | 10 |

DG − CB = −6.0 points hidden (95% CI −12.4 to +0.0, by function).

- **Run g60a (Gate 55's rules) carries the comparison:**
  - CB: 29 cases, 15 corrections, all 15 confirmed on re-show; 12 of 25 decisions right; hidden 59.6%.
  - DG: 10 cases, 2 corrections; 6 of 25 right, the same as the list alone; hidden 47.2%, also equal to the list alone.
  - CB got six decisions right that DG did not:
    - the year-end close;
    - a time after a date tolerated;
    - two slug rules (cut at a word boundary, "untitled" when empty);
    - 0.0 when the old value is zero;
    - a phone number without exactly 10 digits returned unchanged.
  - The 10 disagreement cases were real, but mostly about odd inputs, such as accented titles, wide digits and an extension on a phone number, not the policy.
- **Run g60b (a fresh rule set) could not compare them.** The skimming owner corrected at least one rule in every one of the 10 functions during the list review (14 corrections). The registered design, inherited from Gate 58 and from Hive's hand-over, shows spot checks only for parts the list review left as they were, so neither CB nor DG showed any case. Their sheets equal SL, and their hidden scores (66.4%, 66.8% vs SL 69.2%) differ only by builder noise.
  - A finding for the product: a skimmer who corrects one rule in every area gets no spot checks at all.
  - Run g60b's list review was the strongest yet: from 2 to 14 of 25 decisions right, hidden from 34.8% to 69.2%.
- **Gate 58 replicated (post hoc, run g60a):** CB 12 vs SL 6 decisions right, hidden +12.4 points (Gate 58: 9 vs 4, +15.6).
- **Disagreements, when they occur, point at real errors:** in run g60b, the first build was wrong on 97% of the calls where the builds disagreed; in run g60a, on 37%. They are simply too few.

## Setup

- **Rule sets:**
  - g60a: Gate 55's published rules (seeds 60100, 60200000);
  - g60b: a fresh independent rule-giver (seeds 60300, 60400000; rules now published in `referee/oracle_g60b.py`).
- Predictions pushed before either run (`5a7e0c3`).
- **Stage 1:** two builds with no owner, N0 and B, each 3 builders from the same prompt in separate repositories. `lab/run_gate.py` now builds a config's `stage1` arms alongside the baseline.
- **From the code (never the oracle):**
  - the describer wrote D from N0 (57 and 75 rules);
  - Gate 58's spotter wrote 49 and 45 spot checks;
  - a prober wrote 300 calls from the spec alone (`prompts/prober_brief.md`); both builds ran them (`referee/wings.py`), and they disagreed on 46 and 31;
  - a selector turned each function's disagreements into at most 4 plain cases (22 and 15; `prompts/selector_brief.md`).
- **The same skimming owner, in separate sessions:**
  - SL: D as a rule list;
  - CB: SL, then the spot checks;
  - DG: SL, then the disagreement cases.

  CB and DG used the same code for corrections and re-shows (Gate 58's), and both skipped the functions the list changed: 4 of 10 in g60a, 10 of 10 in g60b.
- **Stage 2:** 3 fresh builders each. The judge labelled every sheet before stage 2.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| W1 | Two builds disagree on ≥ 50% of the first build's errors | **Failed:** 19% (47 of 243) |
| W2 | DG states at least as many decisions right as CB | **Failed:** 20 vs 26 |
| W3 | DG shows at most 70% as many cases as CB | **Held:** 34% (10 vs 29) |
| W4 | Hidden DG ≥ CB − 3 | **Failed:** −6.0 |
| W5 | DG ≥ SL + 2 decisions | **Failed:** 20 vs 20 |
| Ship / Replace | | **Did not fire** |
| Kill | DG ≤ CB − 2 decisions and hidden ≤ CB − 5 | **Fired** |

## What it means

1. **The spotter stays.** It reads the code and asks "what would a business owner decide differently here", and that finds the owner's decisions. A second build only finds where two builders differ, and two builders from one model mostly agree, including on wrong guesses. Disagreement measures the spec's ambiguity *to a builder*, not the gap between a builder's guess and the owner's policy.
2. **Two wings would need different pilots.** The error overlap is the cause, so a second build from a different model (Codex, Gemini) might disagree more. That is untested; Gate 62 measures it mechanically, without an owner.
3. **The skip rule needs a look.** Hive's hand-over shows spot checks only for parts the list review left untouched. An owner who corrects one headline rule per area gets no checks on that area's details, which is where Gate 58's gain came from. A registered test is needed before changing it.

## Limits

- One run per arm per rule set, and run g60b showed no cases, so the comparison rests on one run.
- A synthetic skimmer. The builds share model and prompt.
- Cost about $17: builders $7.1, Hive-side and owner model calls $9.3, the rule-giver extra.

## Files

`prompts/`: prober, selector and judge briefs, plus Gate 58's copies; predictions.

`referee/`:
- `review60.py`, `wings.py`, `analyze.py`;
- `oracle_g60b.py`, published after scoring.

`results/g60a/`, `results/g60b/`:
- sheets, every case shown, the owner's replies and corrections, the probe calls with both builds' outputs (`sheet.json`);
- probes, summaries, ask texts and run logs.

`results/analysis.txt` holds the analysis output.
