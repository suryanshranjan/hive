# Gate 100 predictions: a harder real-code sample, where the summary loses what a builder needs

Registered Nov 2 2026, before any arm runs. Gap 4, second round.

## Why this test

- **Gate 86's ten Django issues were too easy.** One builder lost only one of them to the underspecified summary, so the sample said little about asking.
- **Gate 94:** Hive now treats a technical goal like one builder (no interview, no business review), and its builders can still ask the reporter.
- **This sample is picked where the summary did hurt:** Django issues (3.0–4.2, none from Gate 86) where Ambig-SWE's Claude Sonnet 3.5 resolved the full issue but not the summary.
  - Shuffled with seed 100 and validated as SWE-bench does (`referee/pick100.py`). 10 valid issues were kept; 1 invalid was skipped (`django__django-12155`).

## Setup

- **Arms** (Gate 86's driver, `referee/run100.py`, its own folder `runs/g100`), each issue once:
  - **F:** one builder, full issue;
  - **N:** one builder, summary, no asking;
  - **S:** `hive start` on main (`ce32296`), on the summary, with the simulated reporter (who sees the full issue) at the keyboard.
- Same harness, reporter and scoring as Gate 86. Analysis `referee/analyze.py`, committed now.

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| A1 | N ≤ F − 3 (on this sample the summary hurts today's builder too) | 45% |
| A2 | S ≥ N + 2 (Hive recovers part of it, through builders asking the reporter) | 35% |
| A3 | S's builders ask the reporter on ≥ 5 of 10 issues | 40% |
| A4 | S's median reporter prompts ≤ 5 | 70% |

## Decision rules

- **Claim (A1 and A2):** on real code, Hive's asking recovers underspecified work.
- **A1 holds and A2 fails, with A3 failing:** builders do not ask on technical goals. The next change is to tell them to ask the reporter when the issue leaves the expected behaviour open, as Ambig-SWE found models must be told.
- **A1 fails:** even this sample does not separate modern builders. Gap 4 then needs a codebase the models have not seen.

## Limits

10 issues, one run each, from a repository the models know. About $10.
