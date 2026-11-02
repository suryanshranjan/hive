# Gate 98 results: the lean reader with the helper-following interface check, Nov 2 2026

**Question.** Flown together, do the lean reader (Gate 97) and the interface check that follows helpers keep Hive's own spend near the builders' and every flight right?

**Answer.**
- **Every flight was right:** all five, pass^5 held, median hidden 27, median 28 prompts.
- **A whole feature cost $0.94 and took 4–10 minutes.** Gates 95–96 cost $3.34–3.67 and took 8–16 minutes.
- **Hive's own spend was 1.6× the builders'**, just above the registered 1.5× (F1 failed). The builders happened to be cheap this time ($0.36 against $0.47), and the absolute spend ($0.58 per flight) was within Gate 97's range.
- **The interface check raised no alarm** in five flights: no result shape was changed this time.

| Flights | Hidden | Prompts | Hive's own | Builders | Total per feature | Minutes |
| --- | --- | --- | --- | --- | --- | --- |
| Gates 95–96 (old reader) | all ≥ 25 | median 32 | $3.04 | $0.47 | ~$3.50 | 8–16 |
| Gate 97 (lean reader) | 15, 27, 27, 27, 27 | median 24 | $0.49 | $0.47 | $0.97 | 5–8 |
| **Gate 98 (lean + helper check)** | 27, 27, 27, 25, 27 | median **28** | **$0.58** | $0.36 | **$0.94** | **4–10** |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| F1 | Hive's own ≤ 1.5× builders' | **Failed:** 1.6× ($0.58 vs $0.36) |
| F2 | pass^5 | **Held** |
| F3 | Median hidden ≥ 26 | **Held:** 27 |
| F4 | Median prompts ≤ 35 | **Held:** 28 |

## Where Hive stands (Tiny Shop, synthetic owner)

- **Right:** 15 of the last 15 flights with the ordinary case first (Gates 95, 96, 98), and 1 miss in 20 counting Gate 97, whose cause is now checked.
- **Owner time:** a median of about 28 prompts, from 55 at the start of the gap plan.
- **Cost:** about $1 a feature, of which Hive's own steps are about 60%. That is from $3.70 of Hive's own spend in Gate 85 alone, 4–10× the builders' spend.

## Files

`prompts/`, `referee/` (`flight98.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
