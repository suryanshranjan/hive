# Gate 86 predictions: Hive on a real codebase, by Ambig-SWE's protocol

Registered Nov 2 2026, before any arm runs. Gap 4 of `docs/gap_plan.md`: "works on my real codebase".

## Why this test, and why this way

- **Every Hive gate so far used a toy project, or a library the goal named function by function.**
- **The measuring stick already exists:** Ambig-SWE (Vijayvargiya et al., ICLR 2026).
  - It takes SWE-bench Verified's real GitHub issues and rewrites each into an underspecified summary.
  - A simulated user, who sees the full issue, answers questions only from it.
  - It publishes per-issue results for each model, with the full issue, with the summary alone ("Hidden"), and with the summary plus asking.
- **We reuse its data** (`github.com/sani903/InteractiveSWEAgents`: the 500 issues, their original text, hints and summaries), **SWE-bench's resolve rule** (every FAIL_TO_PASS and PASS_TO_PASS test passes), and **its user-proxy instructions**.
- **We run without Docker**, which this machine cannot start. `referee/swe86.py`: the Django checkout at each issue's base commit, Python 3.9 from uv, Django's own runner, and SWE-bench's log format.

## Setup

- **The sample:** Django issues (SWE-bench Verified versions 3.0–4.2), shuffled with seed 86. Each is validated as SWE-bench does: with the test patch, the FAIL_TO_PASS tests fail before the gold patch and pass with it.
  - 10 valid issues were kept in that order (1 invalid was skipped: `django__django-11276`).
  - PASS_TO_PASS is measured (the tests passing both before and with the gold patch), because the published lists are cut off at Excel's cell limit.
- **Arms**, each issue once:
  - **F:** one builder, the full issue, no asking (the ceiling);
  - **N:** one builder, the underspecified summary, no asking (Ambig-SWE's "Hidden");
  - **S:** `hive start` as shipped, on the summary, with the simulated user at the keyboard. Hive's whole flow is tested: the fast/cheap question, the interview, builders asking, the interface check, the review.
- **Visible tests (all arms):** the test modules the issue's test patch touches, without that patch. Hive's guard needs a suite, and this tells every arm where the tests live (Ambig-SWE found such location hints raise resolve rates).
- **The simulated user:** `claude -p`, Ambig-SWE's instructions plus Hive's terminal conventions (`referee/run86.py`).
- **Builders:** Hive's default (Claude Sonnet 5.5), 30 minutes.
- **Published reference on the same 10 issues** (Ambig-SWE, Claude Sonnet 3.5): full 5/10, Hidden 1/10, with asking 3/10.
- **Order:** F and N for all 10 first (they run beside Gate 85, sharing no state), then S after Gate 85 (it needs `~/.hive`).

## Predictions

| # | Prediction | Odds |
| --- | --- | --- |
| P1 | F resolves ≥ 7 of 10 | 60% |
| P2 | N resolves ≤ F − 2 (the summary hurts) | 55% |
| P3 | S resolves ≥ N + 2 (Hive's flow recovers what the summary lost) | 45% |
| P4 | S resolves ≥ F − 1 (it recovers nearly all of it) | 35% |
| P5 | S's median owner prompts per issue ≤ 15 | 40% |

## Decision rules

- **Claim (P3 and P4):** on real issues in a real codebase, Hive's asking flow recovers underspecified work to nearly full-information level. That is the result Ambig-SWE and "Ask or Assume?" reach with single agents, here with Hive's product flow.
- **P2 fails** (the summary does not hurt modern builders): the issues are too easy or too well known, and the sample says nothing about asking.
- **P5 fails:** the flow is too heavy for a one-issue fix. That feeds Gap 2.

## Limits

- 10 issues, one run each, from one repository the models have likely seen (SWE-bench leakage is known).
- The simulated user is more cooperative than a real reporter.
- About $30–50.
