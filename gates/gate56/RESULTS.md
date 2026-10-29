# Gate 56 results: a short sheet for the skimming owner, Oct 30 2026

**Question.** Gate 55 found that a skimming owner repairs only about a quarter of a code sheet's wrong decisions. Does a short sheet help, one with only the business choices the code made (30 rules instead of 74)?

**Answer.**
- **No. The skimmer caught the same few things either way.**

| Sheet the skimming owner reviewed | Rules shown | Decisions right after review (of 25) | Hidden pass | Replies |
| --- | --- | --- | --- | --- |
| Full (SF) | 74 | 6 (24%) | 42.4% | 9 |
| Short, business choices only (SS) | 30 | 7 (28%) | 42.0% | 10 |
| No owner (N0) | – | – | 35.2% | – |

SS − SF = −0.4 points (CI −8.8 to +10.0).

- **What a skimmer corrects is set by what he remembers, not by what he is shown.** In both reviews he fixed the same headline rules:
  - the late fee's 5-day grace and minimum;
  - the meeting end capped at 23:59;
  - the platinum tier at 20,000.

  He let the rest pass: rounding to 5 cents, what happens to letters in a phone number, negative values. Those are what the hidden tests mostly probe.
- **Skimming is also noisy.** The same owner brief on the same rules gave +29 points over no owner in Gate 55 and +7 here. With a skimmer, the code sheet reliably delivers his few salient rules and little else.
- The short sheet kept 76% of the decisions in view before review (T4), so its brevity did not hide much. It just did not change his reading.

## Setup

- **Rules:** Gate 55's (published after its scoring; builders never see them), with new visible and hidden draws (seeds 56100, 56200000). Predictions pushed before the run (`dbd9e57`).
- **Stage 1:** a fresh N0 build. From its code, two describers wrote D (in full, 74 rules) and DS (business choices only, 30 rules; `prompts/describer_short_brief.md`).
- **Reviews:** the same skimming owner (Gate 55's brief and policy prose) reviewed each, separately, as a terminal rule list. Each sheet then went to 3 fresh builders.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| T1 | The short sheet has at most 35 rules | **Held:** 30 |
| T2 | +15 points of decisions right after review | **Failed:** +4 (7 vs 6 of 25) |
| T3 | SS ≥ SF + 5 hidden | **Failed:** −0.4 |
| T4 | The short sheet addresses ≥ 70% of decisions before review | **Held:** 76% |
| Ship | T2 and T3 | **Did not fire** |
| Kill | SS no better on either | **Did not fire on its letter** (7 vs 6 decisions), but the difference is one decision |

## What it means (Gates 55–56 together)

1. **The code sheet's yield is the owner's attention, and its format barely matters.** Careful: 100%. Skimming: a quarter of the wrong decisions, by list, by conversation, by a short sheet.
2. **A skimmer's salient rules are the ones he would also give in an interview.** What only a careful read catches is the detail: rounding steps, odd inputs, exact cut-offs. Gate 45's founder marked 0 of 46 on day 1: a skimmer.
3. **Next lever (conjecture): ask for attention one concrete outcome at a time, where it is cheap.** Gate 38 found he decides when he sees a concrete outcome. A spot check ("Ravi's ₹90 refund at day 20 comes to ₹0. Right?") on the decisions where the code made a non-obvious choice could buy careful attention a few seconds at a time. That needs the founder.

## Limits

- One run per arm; a synthetic skimmer; the same rule set as Gate 55.

## Files

`prompts/` (both describer briefs, owner, judge, predictions), `referee/` (`review56.py`, analysis), `results/` (both sheets, both reviews, judge labels, probes, costs, run log), `swarms/`, `logs/`.
