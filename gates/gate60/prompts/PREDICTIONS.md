# Gate 60 predictions: two wings (show the owner where two builds disagree)

Registered Oct 30 2026, before the run. Asked for by the user ("Run the tests as required", after the proposal "two wings, compare where they disagree"). Gate 45 and the founder's Telegram are untouched; this is the wind-tunnel test.

## Why this test

Gate 58 shipped the combined review: a skimming owner reviews the rule list, then sees 2–5 spot checks per function that a spotter picked from the built code. It lifted him from 4 to 9 of 25 decisions right, but at the price of 29 cases to read. The spotter guesses which choices matter.

Two independent builds of the same spec make the same choice wherever the spec is clear enough, and different choices where it leaves one open. Where they disagree is, by construction, where the owner's rule is needed. If those cases are the owner's spot checks, he may read fewer cases for the same yield.

The risk: two builds by the same model share defaults. Where both pick the same wrong default, they agree, and the owner is never asked.

## Setup

Two runs, each with these arms:
- **g60a:** Gate 55's published rule set (`gates/gate55/referee/oracle.py`), new draws (seeds 60100, 60200000).
- **g60b:** a fresh rule set from an independent rule-giver (Gate 58's brief), seeds 60300, 60400000.

**Stage 1:** two independent builds of the same spec, with no owner: **N0** and **B** (3 builders each, the same prompt, separate repositories). `lab/run_gate.py` now builds the arms listed in a config's `stage1` alongside the baseline.

From the code (never the oracle):
- the describer writes D from N0 (Gate 58's brief);
- Gate 58's spotter writes spot checks from N0;
- a prober writes 30 calls per function from the spec alone (`prompts/prober_brief.md`), without seeing the code or knowing any answer;
- both builds run every call (`referee/wings.py`);
- for each function, a selector turns the disagreements into at most 4 plain cases ("…: our build charges 2 rupees (a second build charged nothing)"; `prompts/selector_brief.md`). A function where the builds never disagree gets no case.

**The same skimming owner** (Gate 55's brief and policy prose), in separate sessions:
- **SL:** D as a rule list (as Gates 55–58).
- **CB:** SL, then the spot checks: Gate 58's combined review.
- **DG:** SL, then the disagreement cases.

CB and DG skip the functions the list review changed. Each correction is applied on its own, and the case is shown again (Gate 58's machinery, the same code for both).

**Stage 2:** 3 fresh builders each for SL, CB and DG.

**Judge:** labels D, SL, CB, DG and R for every declared decision before stage 2.

Driver: `referee/review60.py`; analysis: `referee/analyze.py` (both committed now). The analysis pools the two runs.

## Predictions (pooled over both runs)

| # | Prediction | Odds |
| --- | --- | --- |
| W1 | Of the prober's calls where N0's result differs from the policy, the two builds disagree on ≥ 50% | 40% |
| W2 | DG states at least as many declared decisions right as CB | 45% |
| W3 | DG shows at most 70% as many cases as CB | 60% |
| W4 | Hidden pass DG ≥ CB − 3 points (mean over the runs) | 50% |
| W5 | DG states ≥ 2 more decisions right than SL (the disagreement cases help at all) | 75% |

## Decision rules

- **Ship:** W2, W3 and W4 hold. Hive draws its spot checks from where two cheap builds disagree, for the same yield with fewer cases. The second build costs money, not owner time.
- **Replace outright:** DG right ≥ CB right + 3 and hidden DG ≥ CB + 5.
- **Kill:** DG right ≤ CB right − 2 and hidden DG ≤ CB − 5. That would mean two builds share their wrong defaults, so disagreement misses what the owner must decide. The spotter stays.
- **Otherwise:** no change to Hive. Report what disagreement found that the spotter missed, and the reverse.

## Limits

- One run per arm per rule set; a synthetic skimmer; the second build uses the same model and prompt, so the builds are less independent than two different teams.
- About $30 for both runs.
