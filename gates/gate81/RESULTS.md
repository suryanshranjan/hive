# Gate 81 results: Gate 76's flights again, after derived areas became the default, Nov 1 2026

**Question.** Gate 80 made areas named from the goal's parts the default. Does the shipped flow still fly, and does it meet Gate 74's business-builder split cleanly?

**Answer.**
- **Two product faults found, both in claiming. Both are now fixed and tested; Gate 82 flies again.**
- **Fault 1: one builder can claim every area.** Areas were derived in both flights (3 each: refunds, loyalty points, sales summary), and in both one builder claimed all 3 at once.
  - Overnight, w2 took the lock `all` and built everything alone. w1 and w3 had nothing they could claim and landed nothing.
- **Fault 2: a refused builder can build and land anyway.** Live, w1's claim was refused ("already held by lock w2"). It built all three parts regardless, and `hive land` accepted the landing, because landing never checked for a lock.
  - All 3 parts were built twice (R3 failed). w2 then found w1's code on main and "kept their source files".
- **The split did not engage live**, so its question was not answered. After the interview (6 rules this time, against 11 in Gate 76), the law chose 2 builders, below the split's 3.
  - With no business builder and no builder asking, the build asked no questions. The full hand-over then ran: a code sheet of 19 rules (5 marked wrong) and 20 spot checks, 71 owner prompts in all (R4 failed; Gate 76 had 26).
- **Accuracy held:** 25 of 27 live and 25 of 27 overnight after the morning (Gate 76: 27 and 22).

| Flight | Builders | Areas | Claims | Hidden | Owner prompts | Builders' cost |
| --- | --- | --- | --- | --- | --- | --- |
| Live | 2 (split off) | 3, derived | w2 claimed all 3; w1, refused, built and landed all 3 anyway | 25 of 27 | 71 | $0.47 |
| Overnight | 3 | 3, derived | w2 claimed all 3; w1 and w3 idle | 17 at night → 25 of 27 after the morning | 10 | $0.60 |

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| R1 | Live: no crash, one branch, ≥ 24 of 27 | **Held:** 25 |
| R2 | Live: areas derived and the split engaged | **Failed:** areas derived (3), but the split did not engage (2 builders) |
| R3 | Live: no part built by 2+ builders | **Failed:** all 3 built by both builders |
| R4 | Live: ≤ 45 owner prompts | **Failed:** 71 (no builder asked, so the full hand-over ran) |
| R5 | Overnight: no crash, ≥ 22 after the morning, fix round ran | **Held:** 25, fix ran |

## What changes in Hive (fixed, tested, to be flown in Gate 82)

1. **A claim may hold at most an even share of the areas:** ⌈areas ÷ builders⌉, so with 3 areas and 3 builders, one each. A larger claim is refused with "claim at most N area(s) at a time, so every builder has work" (`hive/claims.py`, `fair_share`).
2. **`hive land` requires a lock.** When areas are configured, landing under a lock name this builder does not hold is refused, with exit 9: "claim free areas first … if every area is taken, the work is someone else's: stop" (`hive/guard.py`, `hive/claims.py` `mine`). The builder prompt explains exit 9.
3. **Derived areas belong to their goal.** Areas a build derived travel with its branch into `.hive/config.json`. A later build now names its own areas instead of inheriting the earlier goal's (`hive/swarm.py`: derived areas, marked by `area_parts`, do not count as configured).

Tests:
- `tests/test_claims.sh`: landing without a lock is refused; a claim beyond an even share is refused.
- `tests/test_run.sh`: a later build names its own areas.
- All other suites pass.

## Limits

- One flight per mode, with a synthetic owner. The interview's length, and so the number of builders, varies between flights (11 rules in Gate 76, 6 here).

## Files

`prompts/` (owner brief, predictions), `referee/` (`flight81.py`, `analyze.py`).

`results/live/`, `results/overnight/`:
- the owner's whole terminal;
- every prompt and reply;
- scores;
- each builder's final report;
- the run log.
