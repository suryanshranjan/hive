# Gate 63 results: spot checks on the parts the list review touched, too, Oct 30 2026

**Question** (follow-up to Gate 60, under the user's "Run the tests as required"). Hive's hand-over shows spot checks only for the parts the owner's list review left as they were. In Gate 60's fresh rule set the skimmer corrected one rule in every part, so he saw no spot checks at all. Should the parts he touched be spot-checked too?

**Answer.**
- **Yes. All four predictions held, and the ship rule fired.**

| Same skimming owner, same builds' sheets (pooled, 50 decisions) | Decisions right | Hidden pass (mean of 2 runs) | Cases he read |
| --- | --- | --- | --- |
| Rule list (SL) | 18 | 58.2% | – |
| List, then spot checks on untouched parts (CB, Hive until now) | 24 | 63.0% | 29 |
| **List, then spot checks on every part (CA)** | **32** | **70.6%** | 29 + 65 |

CA − CB = **+7.6 hidden points** (95% CI +1.6 to +15.4, by function).

- **A part he corrected for its headline still hid its details.**
  - **Gate 55's rules:** in the list review he fixed the late fee's headline. Shown three late-fee cases, he then caught the 5-day grace, the $5 minimum and the cap at a fifth of the invoice ("No, the fee should be 5 dollars. Our minimum late fee is 5 dollars"). Three more late-fee decisions became right.
  - **The fresh rules:** shown 45 cases over the 10 parts he had touched, he corrected 27. Five more decisions became right: Christmas as a non-working day, a grade cut-off, a price tier, a rating rule and the late fee.
- **Shown again, 36 of 37 corrections were confirmed.** Nothing CB had right was spoiled.
- **The cost is his reading.** In the fresh rule set, the full combined review was 45 cases plus 27 re-shows after the list, against none before. At an assumed 10 s a reply, that is about 12 minutes of a real owner's time (estimate). The synthetic skimmer's model calls cost $5.43. The gain per case is close to Gate 58's: one more decision right per 7 to 9 cases here, against one per 6 in Gate 58.

## Setup

- From Gate 60's own records: the same N0 build, sheet D, spotter cases, owner brief and policy.
  - **g60a** (Gate 55's rules): the list had touched 4 of 10 functions. CA = CB's sheet, then the 20 spot checks of those 4 functions.
  - **g60b** (the fresh rules): the list had touched all 10, so CB equalled SL. CA = SL's sheet, then all 45 spot checks.
- Corrections were applied one at a time and re-shown, using Gate 58's machinery.
- A fresh judge labelled SL, CB, CA and R together.
- 3 fresh builders built CA from Gate 60's starting repo. Its hidden pass is compared with Gate 60's SL and CB builds on the same suite.
- Predictions pushed before the run (`791ea3f`).
- Cost: owner model $7.22, judges $0.70, builders $1.79.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| H1 | CA ≥ CB + 3 decisions | **Held:** 32 vs 24 |
| H2 | Hidden CA ≥ CB + 3 | **Held:** +7.6 |
| H3 | CA spoils ≤ 1 of CB's right decisions | **Held:** 0 |
| H4 | He corrects ≥ 20% of touched-part cases | **Held:** 57% (37 of 65) |
| Ship | H1 and H2 | **Fired** |
| Kill | | **Did not fire** |

## Disclosed

- **The first g60a attempt stopped at the hidden-suite probe** (a relative oracle path, the same fault as Gate 62's) after its owner session and builds. Its sheet was never saved or scored, and g60a was rerun from scratch with a new owner session. g60b ran after the fix.
- **The comparison mixes build times.** CA's builds are new; SL's and CB's come from Gate 60. In g60b, two builds of the same sheet (SL and CB) differed by 2.8 points, which is the scale of builder noise. CA's gain is larger in both runs (+9.6 and +5.6 over CB).
- **The judge labels differ slightly from Gate 60's.** This judge saw SL, CB, CA and R together and gave SL 18 and CB 24 of 50, where Gate 60's judge gave 20 and 26. Comparisons here use this gate's labels only.

## What changes in Hive

The hand-over's spot checks now cover every part: first the parts his review left as they were (Gate 58), then the parts it changed (`spotcheck.order`, used by `hive start`). `HIVE_SPOTS=0` still turns them off.

## Limits

- One synthetic skimmer, and one build of CA per rule set.
- The extra reading is real: up to 45 cases after a list review on a 10-part job. Whether a real founder reads that many is Gate 45's question.

## Files

`prompts/` (judge brief, predictions), `referee/` (`review63.py`, `analyze.py`).

`results/g63a/`, `results/g63b/`:
- every case shown, correction and re-show, CA's sheet and the judge labels (`sheet.json`);
- probes, ask texts, agents and run logs.
