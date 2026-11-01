# Gate 82 results: Gate 81's flights again, after its two claim fixes, Nov 1 2026

**Question.** Do Gate 81's fixes hold in flight: a claim holds at most an even share of the areas, and `hive land` needs a lock?

**Answer.**
- **Both fixes held, and a third gap showed.** Overnight was clean: 3 builders, one area each, nothing built twice.
- **Live, after two builders had landed their parts, each claimed the other's landed area and began rebuilding it.** A landed area's lock is released, so `hive areas` listed it as "free" again. Both noticed and released, and nothing landed twice.
  - Q2 failed: 2 parts were built in 2 builders' own commits.
  - w2's own words: "`hive areas` still listed the report area as free after I landed it, so w1 claimed it too".
- **Live was otherwise the shipped flow at its best:**
  - 3 builders, the split engaged, the business builder (w3) asked 5 questions, and the long review was skipped.
  - 27 of 27 hidden tests, 38 owner prompts (most of them the 18-rule interview).

| Flight | Builders | Locks (areas each) | Builders who landed | Parts built twice | Hidden | Owner prompts |
| --- | --- | --- | --- | --- | --- | --- |
| Live | 3, split on | 6 locks, 1 area each | w1, w2, w3 | 2 (landed areas reclaimed) | 27 of 27 | 38 |
| Overnight | 3 | 3 locks, 1 area each | w1, w2, w3 | 0 | 17 → 25 of 27 after the morning | 16 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| Q1 | Live: no crash, one branch, ≥ 24 of 27 | **Held:** 27 |
| Q2 | Both flights: no part built by 2+ builders | **Failed:** live 2 (landed areas reclaimed), overnight 0 |
| Q3 | Both flights: claims within an even share; ≥ 2 builders landed | **Held:** every lock 1 area; all 3 builders landed in each |
| Q4 | Overnight: no crash, ≥ 22 after the morning, fix ran | **Held:** 25, fix ran |
| Q5 | Both flights: all three functions delivered | **Held** |

## What changes in Hive (fixed, tested, to be flown in Gate 83)

- **A landed area shows as landed, not free.** Within a build, `hive land` records the areas it released (in the run's folder, not in git).
  - `hive areas` shows "landed by w1".
  - `hive claim` refuses a landed area unless the builder passes `--again`, which is only for fixing something it found wrong there.
- **Where:**
  - `hive/guard.py` (`_remember_areas`, `_landed`, `landed`);
  - `hive/claims.py`;
  - `hive/__main__.py` (`--again`);
  - the builder prompt.
- **Test:** `tests/test_claims.sh`, where a landed area is refused, shown as landed, and claimable with `--again`. All other suites pass.

## Limits

- One flight per mode, with a synthetic owner.

## Files

`prompts/`, `referee/` (`flight82.py`, `analyze.py`).

`results/live/`, `results/overnight/`:
- the terminal, prompts and replies;
- scores;
- each builder's report;
- the run log.
