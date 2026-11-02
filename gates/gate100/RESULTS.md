# Gate 100 results: a harder real-code sample, Nov 2 2026

**Question.** Gate 86's Django issues were too easy to test asking. On issues where the summary did hurt a 2025 model (Ambig-SWE's Claude Sonnet 3.5 solved the full issue but not the summary), does it hurt today's builder, and does Hive's flow recover what it loses?

**Answer.**
- **The summary did not hurt today's builder at all.**
  - One builder resolved 9 of 10 with the full issue and 9 of 10 from the summary alone (A1 failed). These are issues where Sonnet 3.5 went from solved to unsolved.
  - Hive's flow also resolved 9 of 10, with a median of 0 reporter prompts, for $0.11–0.35 an issue.
  - No builder asked the reporter anything (A3 failed). None needed to.
- **All three arms failed the same issue,** `django__django-14140`.
- **The registered rule for A1 failing applies:** even this sample does not separate modern builders. These SWE-bench issues are public and well known (leakage is documented), and today's models solve their summaries. Gap 4's question, whether Hive helps on real code where the intent is unclear, needs a codebase and issues the models have not seen.

| Arm (10 harder Django issues) | Resolved | Reporter prompts | Cost per issue |
| --- | --- | --- | --- |
| One builder, full issue (F) | 9 | 0 | about $0.10–0.20 |
| One builder, summary (N) | 9 | 0 | about $0.10–0.20 |
| `hive start`, summary (S) | 9 | median 0 (the fast/cheap question at most) | $0.11–0.35 |
| *Ambig-SWE Claude Sonnet 3.5, published* | *full 10, summary 0 by selection* | | |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| A1 | N ≤ F − 3 | **Failed:** 9 vs 9 |
| A2 | S ≥ N + 2 | **Failed:** 9 vs 9 |
| A3 | S's builders ask on ≥ 5 issues | **Failed:** 0 |
| A4 | S's median prompts ≤ 5 | **Held:** 0 |
| Claim | A1 and A2 | **Did not fire** |

## What it means

1. **For technical goals, Hive behaves like one builder** in accuracy (9 = 9), the reporter's time (0 prompts) and roughly cost. This confirms Gate 94.
2. **Public benchmarks cannot test owner intent with today's models.** The summaries no longer hide anything a model needs. The test that remains is the one only real owners and private code can give: the founder session (`docs/founder_session.md`).

## Files

`prompts/`, `referee/` (`pick100.py`, `run100.py`, `analyze.py`).

`results/<arm>_<issue>/`:
- the result;
- the builder's report for F and N;
- the terminal and prompts for S.

`results/analysis.txt`.
