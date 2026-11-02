# Gate 99 results: the overnight path, after everything since Gate 83, Nov 2 2026

**Question.** Every change since Gate 83 was flown live only. Does the overnight path (`hive start --overnight`, then `hive morning`) still work, and how reliable is it?

**Answer.**
- **It works and is cheap**, with no crash in five flights:
  - $1.09 per feature (builders $0.89–1.03, Hive's own $0.13–0.20);
  - 3–5 minutes of build;
  - a median of 14 morning prompts (N3, N4 held);
  - median hidden 25 after the morning (N2 held).
- **But only 3 of 5 succeeded** (pass^1 0.60; N1 failed). Live flights now succeed 5 of 5.
- **The two failures (23 and 21 of 27) missed the same decisions:**
  - the half refund from day 15 to 30 (3 refund cases);
  - final-sale double points;
  - and in one, the 500-rupee points minimum.
- **No night builder recorded a question about them.** The three builders recorded 12–14 questions between them, on other things.
- **It is the overnight gap Gates 76–77 found:** overnight there is no interview (MAST FM-2.2, fail to ask for clarification), and splitting the night builders did not fix it (Gate 77).

| Flight | Night | After the morning | Morning prompts | Minutes | Cost |
| --- | --- | --- | --- | --- | --- |
| overnight1 | 16 | 26 | 13 | 3.5 | $1.03 |
| overnight2 | 6 | **23** | 14 | 3.6 | $1.17 |
| overnight3 | 11 | 25 | 19 | 4.7 | $1.11 |
| overnight4 | 17 | 26 | 15 | 4.4 | $1.11 |
| overnight5 | 17 | **21** | 12 | 3.2 | $1.05 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| N1 | pass^1 ≥ 0.8 | **Failed:** 0.60 |
| N2 | Median after the morning ≥ 25 | **Held:** 25 |
| N3 | Median morning prompts ≤ 20 | **Held:** 14 |
| N4 | Mean cost ≤ $1.50 | **Held:** $1.09 |

## Disclosed

- During these flights a guard fix shipped (`803fecf`): the guard now deletes its temporary snapshot after each landing. It changes no result, only disk use. Every landing had been leaving its snapshot behind, 800 in a day, which filled the disk at 05:59.

## What changes

- **Next (Gate 102): the interview before an overnight build.**
  - The owner is at the keyboard when he types `hive start --overnight`, so the interview the live path uses can run then.
  - The night builders get his rules, and the morning questions cover only what is left.
  - It is the registered next candidate since Gate 77.

## Files

`prompts/`, `referee/` (`flight99.py`, `analyze.py`).

`results/overnight1` to `results/overnight5`:
- the terminal, prompts and replies;
- scores;
- the run log.
