# Gate 2 results (Oct 27 2026)

Three silent swarms (2, 6 and 12 long-lived Claude workers) extended the same engine from 362 to 1,340 passing visible tests across 99 open feature categories. They ran concurrently, with SQLite as referee and lock-file claims through `tools/claim.sh`. Every swarm finished the whole project. Hidden tests (2,260 new and 700 old, disjoint seeds) were never visible to workers.

| Swarm | Workers | Tokens | Minutes to all 1,340 | Speed vs 2 workers | Tokens per category | Rebase conflicts per landing | Regressions on main | Hidden 2,260 / old 700 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N2 | 2 | 515k | 17.7 | 1.0x | 5.2k | 0.14 (2 of 14) | 0 | 2,260 / 700 |
| N6 | 6 | 963k | 8.2 | 2.2x | 9.7k | 0.33 (6 of 18) | 0 | 2,260 / 700 |
| N12 | 12 | 1.62M | 7.8 | 2.3x | 16.4k | 0.48 (10 of 21) | 1, lived 22 s | 2,260 / 700 |

## Predictions registered before launch, scored

| # | Prediction | Result | Verdict |
| --- | --- | --- | --- |
| 1 | Tokens follow c_on N + c_task T with c_on 101k, c_task 5k: 697k, 1.10M, 1.71M; kill if off by more than 1.5x | 515k, 963k, 1.62M (0.74x to 0.95x). Refit: 111k per worker + 3.0k per category, within 0.5% on all three (2 parameters, 3 points) | Held |
| 2 | Speed of 12 vs 2 workers about 3 to 4x | 2.3x; 6 to 12 workers bought 5% speed for 69% more tokens | Failed |
| 3 | Conflicts per landing about 0.15, 0.75, 1.6 (kappa (N-1)) | 0.14, 0.33, 0.48: grew roughly as N^0.7, not linearly; workers put new features in their own modules | Failed |
| 4 | Visible and hidden pass rates within 2 points at every commit | Within 0.4 points at every commit of all three swarms | Held |
| 5 | Long sessions make per-task cost grow faster than linear | 2-worker sessions covered about 50 categories each for 246k to 269k tokens, on the linear model | Not supported |

## New observations

- **First semantic conflict.** At N = 12, three workers each added a helper named `Parser.word()` with different behaviour. Git merged them without a textual conflict, the last definition won, and main fell from 980 to 439 visible tests (1,540 to 486 hidden). The author's pre-push check caught it and the fix landed 22 seconds later. None at N = 2 or 6.
- **Duplicate work from free-text claims.** At N = 6, two workers built UPDATE FROM, multi-column SET and transactions under different lock names. Claims should name test categories, not free text.
- **Saturation by the biggest task.** Workers bundled categories into 13 to 21 tasks; the largest (window functions, JSON, dates) took 6 to 7 minutes each, which floors the finish time near 7.8 minutes however many workers join. The span limit predicts saturation near 1.5 W / D, about 7 workers here.
- **An interrupted launch** (stopped by hand after 5 minutes) is kept in `aborted_run/` and excluded from all results.
