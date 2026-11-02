# Gate 97 results: a lean reader for Hive's own calls (Gap 3), Nov 2 2026

**Question** (the user: "Hive's own model calls still cost 4–10× the builders' … Fix it"). Most of Hive's own spend was not the reading itself. Each call ran Claude Code's full coding-agent setup and re-cached about 11,000 tokens of system prompt and tool definitions. With the same model, no tools, and a one-line system prompt, run in an empty folder, does Hive's own spend fall without losing accuracy?

**Answer.**
- **Yes. The claim fired.**
- **Hive's own spend fell to 0.16×:** $0.49 per flight against $3.04. It now about equals the builders' spend (1.0×, from 6.5×).
- **A whole feature now costs about $0.97,** against $3.34–3.67 in Gates 95–96.
- **Flights were faster:** 4.8–8.0 minutes against 8.3–15.7, since each reading call takes about 2 seconds instead of 4–5.
- **Accuracy held by the registered measures:** pass^1 0.80, median hidden 27, median prompts 24 against 32.
- **pass^5 failed (live1: 15 of 27).** The cause was not the reader, but a gap in the interface check, found and fixed below.

| Flights | Hidden | Prompts | Hive's own | Builders | Total per flight | Minutes |
| --- | --- | --- | --- | --- | --- | --- |
| Gates 95–96 (old reader) | 10 of 10 ≥ 25 | median 32 | mean $3.04 | $0.47 | $3.34–3.67 | 8.3–15.7 |
| **Gate 97 (lean reader)** | 15, 27, 27, 27, 27 | median **24** | mean **$0.49** | $0.47 | **$0.97** | **4.8–8.0** |

- **Where Hive's own spend goes now:** reading free-text replies ($0.44 over five flights), settling answers ($0.43), writing rules ($0.32), amending them ($0.25), and smaller steps.

## Why live1 failed: the interface check could not see through a helper

- After an owner answer about mixed payments, the builder built `refund()` as `return _split(order, …)`. The helper `_split` returns `{'amount', 'method', 'card', 'store_credit'}`, so all 12 hidden refund tests fail (15 of 27).
- The interface check read the goal correctly (`refund` in `shop/refunds.py`, result keys `amount`, `method`). But it looked only at dict literals returned directly inside `refund()`, so the helper's result went unseen.
- **This is Gate 83's and Gate 90's failure, by a third path.**

**Fixed:**
- The check now follows a `return helper(...)` into a helper in the same file, two levels deep (`hive/contract.py`), with a unit test.
- **Replayed on all 51 delivered Tiny Shop builds from Gates 76–97,** it flags 4:
  - three of them are the three failures of this kind (Gate 83 14/27, Gate 90 live5 15/27, Gate 97 live1 15/27), each of which it would now send back to be put right;
  - the fourth (Gate 87 live1) returns an extra `status` key on an edge path the hidden tests never reach. The flag is correct by the goal's words, and the fix it would trigger is harmless.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| E1 | Hive's own spend ≤ 0.3× Gates 95–96's | **Held:** 0.16× |
| E2 | pass^1 ≥ 0.8 | **Held:** 0.80 |
| E3 | Median hidden ≥ 26 | **Held:** 27 |
| E4 | Median prompts ≤ 1.2× | **Held:** 24 vs 32 |
| E5 | pass^5 | **Failed:** live1 (interface check gap) |
| Claim | E1, E2 and E3 | **Fired** |

## What changes in Hive

1. **The lean reader stays the default** (`hive/explain.py`). `HIVE_EXPLAIN_CMD` overrides it.
2. **The interface check follows helpers in the same file** (`hive/contract.py`). Gate 98 flies both together.

## Files

`prompts/`, `referee/` (`flight97.py`, `analyze.py`).

`results/live1` to `results/live5`:
- the terminal, prompts and replies;
- scores and spend by step;
- the run log.
