# Gate 104 results: confirm the owner's rules once, at the end, Nov 3 2026

**Question** (Gap 2, owner time; run because the user asked for everything that needs only the computer). After the interview, Hive reads each answer the owner gave in his own words back to him, one at a time, and then shows all the rules together on one sheet. Is the sheet alone enough, so he answers fewer prompts with nothing lost?

**Answer.**
- **Yes. All three predictions held, and the ship rule fired.** Confirming once is now the default.
- **Prompts:** the median owner prompts per flight fell from 30 to 23.
- **Nothing was lost:** all six builds passed 27 of 27 hidden tests.

| Flight | Hidden | Prompts | Read-backs | Rule sheet and its fixes | Builder questions | Review spot checks | Minutes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 (each answer read back) | 27 / 27 | 30 | 7 | 2 | 5 | – | 12.9 |
| P2 | 27 / 27 | 30 | 8 | 3 | 6 | – | 13.1 |
| P3 | 27 / 27 | 42 | 10 | 8 | 2 | 6 | 19.5 |
| B1 (confirmed once) | 27 / 27 | 36 | 0 | 16 | 1 | 6 | 16.2 |
| B2 | 27 / 27 | 20 | 0 | 5 | 3 | – | 10.5 |
| B3 | 27 / 27 | 23 | 0 | 2 | 7 | – | 12.4 |

(Prompt kinds were counted after the run, from the owner logs: `results/prompts_by_kind.txt`. The pace question and interview questions make up the rest.)

## Predictions scored (registered code: `referee/analyze104.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| Q1 | B saves at least 5 owner prompts (median) | **Held:** 7 (30 vs 23) |
| Q2 | Every B flight ≥ 24 of 27 | **Held:** 27, 27, 27 |
| Q3 | B's median hidden ≥ P's minus 1 | **Held:** 27 vs 27 |
| Ship | Q1, Q2 and Q3 | **Fired** |
| Kill | | **Did not fire** |

## What it means

1. **The read-backs were mostly double work.** Without them, Hive's misreadings surface on the rule sheet instead: in B1 the owner marked 3 interview rules wrong there, each fixed with one "What should it be?". So the saving is not the full 7–10 read-backs but what remains after the sheet's extra fixes: about 7 in the median.
2. **The biggest swing in owner prompts is not this setting.** Hive skips the after-build review only when builders asked 3 or more questions (Gate 68). In P3 and B1 they asked 2 and 1, so the full review ran, and those flights cost 42 and 36 prompts. Compared like with like (no review), P took 30 and 30 and B took 20 and 23. The next lever on owner time is the review that runs when builders ask little.
3. With 3 flights an arm and builders' questions varying this much, the 7-prompt saving is a measurement, not a precise constant.

## What changes in Hive

`hive/interview.py`: own-words answers are no longer read back one by one when the rule sheet will follow (two or more rules). The sheet is the one confirmation. If no model can merge the answers into rules, the sheet still shows them as read, so he always confirms once. `HIVE_CONFIRM_EACH=1` brings the read-backs back.

## Setup and limits

- Gate 103b's live flight on Tiny Shop, Gate 54's goal, published policy and 27 hidden tests, with a synthetic owner.
- Run Nov 3 on the user's laptop in the Docker lab container, from an empty `~/.hive`, in the order P1 B1 P2 B2 P3 B3. Hive's examples check was on in both arms.
- Predictions pushed before the first flight (`e779e52`).
- One synthetic owner, one goal, 3 flights an arm.

## Files

`prompts/` (owner brief, predictions), `referee/` (`flight104.py`, `analyze104.py`), `results/`:
- each flight's record, owner log, terminal and run log;
- the analysis;
- prompts by kind.
