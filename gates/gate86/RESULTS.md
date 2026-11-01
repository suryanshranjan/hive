# Gate 86 results: Hive on a real codebase, by Ambig-SWE's protocol, Nov 2 2026

**Question** (Gap 4). On real GitHub issues in a real codebase (SWE-bench Verified, Django), given only an underspecified summary, does Hive's flow recover what one builder alone loses? And at what cost to the reporter's time?

**Answer.**
- **No. The claim did not fire.**
- **The summary barely hurt today's builders.** One builder resolved 8 of 10 with the full issue and 7 of 10 from the summary alone (P2 failed). On these 10 issues there was little left to recover.
- **Hive's flow (`hive start`) resolved 8 of 10:** the one issue the summary lost, back, and nothing more.
- **It cost about 15× as much** ($19.72 against $1.34 for the full-issue builder), and the reporter answered a median of 23.5 prompts per one-issue fix.
- **The worst finding is the interview.** Hive's interview is built to ask a business owner about his rules, and on Django bugs it invented a business to ask about. Two examples:
  - for an ORM bug in `deferred_to_data` (django__django-14765): "A customer pays Rs 5,000 for an order, then cancels 3 days later…";
  - for a `select_related()`/`only()` bug on a proxy model: "Priya at the front desk opens the 'Wholesale customers' list…".

  The simulated reporter answered "I don't have that information" 96 times across the 10 issues (44 times on one).

| Arm | Resolved (of 10) | Cost, all 10 | Reporter prompts (median) |
| --- | --- | --- | --- |
| F: one builder, full issue | **8** | $1.34 | 0 |
| N: one builder, summary only | **7** | $1.23 | 0 |
| S: `hive start`, summary, reporter at the keyboard | **8** | $19.72 (builders $3.41, Hive's own $16.31) | 23.5 (15–70) |
| *Ambig-SWE, Claude Sonnet 3.5, same 10 issues (published)* | *full 5, hidden 1, with asking 3* | | |

- **Per issue:** S recovered `django__django-13513` (summary 0, Hive 1). All three arms failed `15022` and `15252`.
- **Compared with the published numbers:** in 2025, Claude Sonnet 3.5 fell from 5 to 1 on these issues when given the summary, and asking brought it back to 3. Today's builder falls from 8 to 7.
  - Underspecified summaries of well-known Django issues no longer separate the arms. The models may also have seen these issues (SWE-bench leakage is documented).
  - To test asking on real code, the next sample has to be issues whose summaries lose what a builder cannot work out alone.

## Setup

- **Data:**
  - Ambig-SWE's release (github.com/sani903/InteractiveSWEAgents): SWE-bench Verified with each issue's original text, hints and underspecified summary, and per-issue published results.
  - The sample: 10 Django issues (versions 3.0–4.2, seed 86), each validated as SWE-bench does. 1 invalid issue was skipped.
- **Harness without Docker** (`referee/swe86.py`):
  - the Django checkout at the base commit, Python 3.9 from uv, and Django's own runner with SWE-bench's log format;
  - resolved means every FAIL_TO_PASS test passes, and every test passing before and with the gold patch still passes.
- **Arms:** F, N and S as registered. **The reporter:** `claude -p` with Ambig-SWE's user-proxy instructions. **Visible tests:** the touched test modules without the test patch, the same for every arm.
- Predictions pushed before any arm ran (`4118202`).

## Predictions scored (`referee/analyze.py`, written after the runs; it applies the registered wording)

| # | Prediction | Result |
| --- | --- | --- |
| P1 | F ≥ 7 of 10 | **Held:** 8 |
| P2 | N ≤ F − 2 | **Failed:** 7 vs 8 |
| P3 | S ≥ N + 2 | **Failed:** 8 vs 7 |
| P4 | S ≥ F − 1 | **Held:** 8 vs 8 |
| P5 | S median reporter prompts ≤ 15 | **Failed:** 23.5 |
| Claim | P3 and P4 | **Did not fire** (and P2's rule applies: the sample says little about asking) |

## Disclosed

- **A scorer bug, fixed after the first runs and before any scoring was used.** The scorer ran `git apply` inside Hive's own repository, which silently skipped the test patch, so every issue scored as unresolved. It now scores in its own repository and resets the test patch's files to the base commit first, as SWE-bench does.
  - Every finished run was rescored.
  - The scorer was checked: the unfixed base scores unresolved, and a builder's real fix scores resolved.
- **No analysis code was committed with the predictions.** `referee/analyze.py` was written after the runs and applies them as worded.

## What it means

1. **Hive's owner interview must not run on a technical goal.**
   - It is built to find a business owner's rules ("who pays what, cut-offs, rounding"). On a bug report it invents a shop, and the person answering wastes their time on it.
   - A first fix, to be tested: when the decisions planned for a goal are not business decisions, skip the interview. Builders can still ask, and the reviews still run.
2. **For a well-specified technical fix, one builder is the right tool.** On these issues `hive start` added cost and the reporter's time without adding accuracy.
3. **For Gap 4 to test asking on real code,** the sample must be issues where the summary loses information a builder cannot infer. Ambig-SWE's own annotations (`LLM_underspecificity_annotation.xlsx`, a "missing information" note per issue) can select them. The data has 231 Django issues; this gate used 10.

## Limits

- 10 issues, one run per arm, from one repository the models have likely seen.
- The reporter was a model, more cooperative than a real one, and it saw the full issue.

## Files

`prompts/PREDICTIONS.md`.

`referee/`:
- `swe86.py` (harness and validation), `run86.py` (arms and scoring), `analyze.py`.

`results/<arm>_<issue>/`:
- the result;
- for F and N, the builder's report;
- for S, the reporter's terminal and every prompt and reply.

`results/analysis.txt`.
