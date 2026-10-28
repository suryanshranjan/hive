# Gate 39 predictions: a wind tunnel for Hive's interview

Registered Oct 29 2026, before the rules exist. Gate 38 (the founder's rule-sheet stability test) is untouched: this gate uses no founder, no Telegram and none of Gate 38's files.

## Why this test

Gates 36 and 37 flew the whole machine with a real pilot, and each crash mixed two causes: what Hive asked (coverage) and how the owner answered (framing, consistency). Gate 38 now tests the pilot. This gate tests the machine alone, the way the Wrights tested wings in a wind tunnel before flying them:

- Hold the pilot perfect: a **synthetic owner** who holds the exact rules (the oracle) and may run them to check any case. He answers every prompt Hive shows, on the same screen a terminal user sees.
- Run **Hive's interview exactly as shipped** (`hive.interview.interview`: decisions from the goal, at most 20 situations, readings, the rule sheet with disagreements and corrections) and give builders the confirmed rules in exactly the words `hive start` uses.
- Measure how much lift it delivers against two references, and where it leaks: not asked (coverage), asked but written wrong (transfer), or written right but not built (builders).

If Hive's interview keeps most of the owner's-tour gain here, the remaining loss in real use is the owner, and Gate 38's line is the right one. If it leaks here, no owner can fix it, and the leak tells us what to change next.

## Setup

- **Rules:** a fresh independent rule-giver (`rulegiver_brief.md`): 10 functions (9 scalar, 1 aggregate) with 25 policy decisions an engineer cannot guess (2 functions carry 1, 3 carry 2, 3 carry 3, 2 carry 4), plus one worked example per decision. Kept private until scored.
- **Suites:** 2 visible typical examples per function (seed 39100); hidden 250 tests, 25 per function, 70% edge calls (seed 39200000). Never committed.
- **Teams** (3 builders each, 40 minutes, no questions to anyone; `prompts/prompt_builder.md`):
  - **N0:** spec and examples only.
  - **H:** plus the rules from **Hive's interview** with the synthetic owner (`referee/wind_tunnel.py`, `prompts/owner_brief.md`).
  - **R:** plus the owner's **complete rule sheet**, written by the owner from his rules (`prompts/documenter_brief.md`): every decision as a rule, no examples. Same wording around the rules as H. The ceiling for any rule-sheet channel.
  - **T:** plus the owner's **decision tour** (one worked example per decision, as visible tests; Gates 13 to 17).
- **Judge** (`prompts/judge_brief.md`), run before any build result exists: for each of the 25 declared decisions, was it asked in the interview, and does each sheet state it right, partly, wrong or not at all.
- **Analysis:** `referee/analyze.py`, committed now. K = (H − N0) / (T − N0) in hidden pass: the share of the tour's gain that Hive's interview keeps.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| W1 | T fixes ≥ 0.85 of N0's edge errors (the tour replicates: 0.94 to 0.98 before) | 80% |
| W2 | R ≥ T − 5 points: complete prose rules carry as much as examples (Gate 15: fully written functions fixed 1.00) | 60% |
| W3 | 0.40 ≤ K ≤ 0.80 (point guess 0.60): Hive's interview keeps a real but partial share of the tour's gain | 50% |
| W4 | The interview asks about 50 to 85% of the 25 decisions, and sheet H states ≥ 80% of the asked ones right | 40% |
| W5 | N0 below 65% | 85% |
| Kill | K < 0.25: with a perfect owner, Hive's interview barely beats no owner at all | 10% |

## Decision rules (what each outcome changes in Hive)

- **K ≥ 0.85:** the interview is not the leak with a consistent owner. No change to the interview; the remaining work is the owner's consistency (Gate 38).
- **Coverage < 0.6 with transfer ≥ 0.8:** the leak is what Hive asks. Gate 40 tests a coverage fix, registered after this gate is scored.
- **Transfer < 0.7:** the leak is writing his answers as rules. Gate 40 tests shipping the answered situations themselves as worked examples beside the rules.
- **R < T − 10:** even complete prose rules lose to examples. Hive should turn every confirmed rule into worked examples the owner confirms.

## Cost and limits

- About $18: 12 builders at about $1, the rule-giver, the documenter, the synthetic owner (one headless call per prompt) and the judge.
- One run per team, one rule set, 10 functions: intervals will be wide.
- The synthetic owner is perfectly consistent and never tired, so this is the machine's ceiling, not a real owner's result. The rule-giver, owner, judge and builders are the same kind of model.
