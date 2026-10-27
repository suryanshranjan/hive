# Hive

Research on swarms of AI coding agents that coordinate only through a shared repository, never by messaging. This repo holds the code, data and swarm histories behind **Hive v2: the referee is the limit** (`docs/hive_v2.md`, live [doc](https://claude.ai/artifact/PZKUKvJY6a7C3dG8ZJrT8H)). The original Hive v1 write-up is in `docs/hive_v1.md`.

**Start with [`BRAIN.md`](BRAIN.md)**, the shared memory of the project: what we know and how sure we are, every prediction and whether it held, open questions, the next experiments, and how to continue.

## What the evidence says so far (Oct 27 2026)

| Finding | Evidence | Strength |
| --- | --- | --- |
| Collisions between agents are rare and cheap: 5% of concurrent pairs touch the same lines, each costs about a quarter of a restart | Anthropic's C compiler history, 2,043 task leases | One real project |
| A swarm ships with main almost never fully green, but live bugs stay small and don't accumulate (mean 5 of 620 hidden tests) | Gate 0: compiler history rebuilt at 415 commits against 620 hidden tests | One real project |
| Bugs are bimodal: 83% caught in about 0.3 h, 17% unseen by the swarm for 7 to 142 h | Gate 0 fine windows | One real project |
| Honest agents did not game the tests: visible and hidden pass rates matched at every commit | Gate 1: 34 Claude workers in 6 swarms | Small project |
| Tripling builders from 2 to 6 bought 1.26x speed; the critical path bound first | Gate 1 | Small project, few runs |
| Each worker costs about 101k tokens to onboard and about 5k per task; 84 to 93% of tokens went to onboarding | Gate 1, fitted on 14 workers, predicted held-out runs within 12% | Small project |
| Foundation-first scheduling made swarms slower and costlier (prediction failed) | Gate 1, two runs each arm | Small project |
| Breakers found one in-scope bug class, then mostly expanded scope | Gate 1 Arm B | One run |
| Onboarding law replicated on a 10x project: tokens = 111k per worker + 3.0k per category (predicted 101k + 5k) | Gate 2: 2, 6, 12 workers, 99 categories | 3 swarms, 1 run each |
| Speed saturates near 6 workers: 2.2x at 6, 2.3x at 12, floored by the largest task | Gate 2 | 3 swarms |
| Collisions grew slower than predicted (0.14, 0.33, 0.48 per landing); first semantic conflict at N = 12, repaired in 22 s | Gate 2 | 3 swarms |
| Still no gaming: hidden and visible within 0.4 points at every commit | Gate 2 | 3 swarms |
| Onboarding law held a third time: 1.61M tokens at 12 workers (predicted 1.63M), 1.23M at 8 (predicted 1.19M) | Gate 3 | 2 swarms |
| Guarded landing blocked both would-be regressions before they reached main; both swarms pass all 2,960 hidden tests with no gaming (gap ≤ 0.4 points) | Gate 3 | 2 swarms |
| Finish time is set by the tail: 12 workers took 8.7 min (Gate 2: 7.8), the last 4% done by one worker who claimed a big task late | Gate 3 | 2 swarms |
| Intent is binding: on invented rules, hidden pass was 58% / 87% / 98% with 0 / 30 / unlimited questions to a product owner; all 40 visible examples passed in every swarm | Gate 3 | 3 swarms of 3 |
| Intent enters only where someone asks: edge cases right 96% on functions someone asked about, 76% on the rest (observational); unlimited access still missed the rules no question touched | Gate 3 | 3 swarms of 3 |
| 30 questions add about 29 points of hidden correctness on a second rule set (48% → 77%); a planner choosing the 30 questions by coverage did no better (76.4% vs 76.8%); the registered prediction failed | Gate 4 | 3 teams of 3, plus a planner |
| On an independent rule-giver's rules, 30 questions added +32 points (35% → 67%); asking about defaults first did no better (62.2%); the registered prediction failed | Gate 5 | 3 teams of 3 |
| Per function: 0 questions gain nothing, the first question adds about +20 points of edge accuracy, three or more about +34 (observational) | Gates 3 to 5 | 100 team-function pairs |

## Layout

| Path | Contents |
| --- | --- |
| `real_repos/` | Analysis of the C compiler's git history: leases, collision rates, collision cost (`ccc_*.py`, `parse_*.py`) |
| `sim/` | Simulator v2 (`hive_sim.py`) and experiments A to D with held-out tests |
| `gate0/` | Replay of the compiler history against hidden suites: scripts, per-commit results, `gate0_results.json` |
| `gate1/referee/` | Test generators with SQLite as referee (`gen.py`, `fuzz.py`), replay evaluator, referee runner |
| `gate1/prompts/` | Exact worker, breaker and founder prompts |
| `gate1/swarms/*.bundle` | Full git history of every swarm: pilot, A, B, A2, F1, F2 (`git clone gate1/swarms/A.bundle`) |
| `gate1/results/` | Per-commit visible and hidden scores for each swarm; `tokens.csv` per worker |
| `gate1/logs/` | Every worker's CLAIM, LAND, CONFLICT and FOUND events |
| `gate2/` | 113-category project: seed bundle, worker prompt, predictions registered before launch, `RESULTS.md` scoring them, all three swarm histories, per-commit hidden scores, `tokens.csv` |
| `gate3/` | Protocol v2 (`tools/claim.py`, `tools/land.py`), the scale runs at 8 and 12 workers, and the intent test (private rules in `referee/oracle.py`, every question asked, call-by-call scores); see `gate3/README.md` and `RESULTS.md` |
| `gate4/` | Planned vs free questions on fresh invented rules: oracle, planner prompt and plan, every question asked, histories, scores; see `gate4/RESULTS.md` |
| `gate5/` | Defaults-first vs free questions on rules from an independent rule-giver agent; see `gate5/RESULTS.md` |
| `BRAIN.md` | Shared memory: laws with status, constants, evidence, scorecard, next steps |
| `docs/` | Hive v1 and Hive v2 write-ups |

## Reproducing

Hidden test suites are deliberately not committed, so future agents working in this repo can't read them. Regenerate them from the fixed seeds:

```
python3 gate1/referee/gen.py hidden_big 9000 50        # 700 template tests
python3 gate1/referee/fuzz.py hidden_fuzz 77000 600    # 600 combined queries
python3 gate2/referee/gen2.py hidden2 5000000 20       # 2,260 Gate 2 tests
python3 gate1/referee/evaluate.py <swarm repo or bundle clone> hidden_big out.json hidden_fuzz
```

Gate 0 needs `anthropics/claudes-c-compiler`, `c-testsuite/c-testsuite`, and the GCC torture tests (`gcc/testsuite/gcc.c-torture/execute`); see `gate0/replay.sh`.

## Gate 2 in one line

Two workers finished the whole 10x project in 17.7 minutes for 515k tokens; twelve finished in 7.8 minutes for 1.62M. See `gate2/RESULTS.md`, including two registered predictions that failed.

## Gate 3 in one line

Category claims and a landing guard kept main clean at 8 and 12 workers, and the token law held again. Finer claims did not make the swarm faster, because the last large task was claimed late. Swarms building invented business rules passed every visible example. On hidden tests they reached 58% with no one to ask, 87% with 30 questions and 98% with unlimited questions. See `gate3/RESULTS.md`.

## Gate 4 in one line

On a fresh set of invented rules, 30 questions again added about 29 points (48% to 77%). A planner choosing the 30 questions by coverage, and turning each answer into a test, did no better than free asking (76.4% vs 76.8%), so the registered prediction failed. Both teams missed the same rules: NULL handling and caps on extreme values. See `gate4/RESULTS.md`.

## Gate 5 in one line

An independent agent wrote the rules. A team told to ask about its defaults first (NULL, extremes, invalid input) did no better than free asking (62.2% vs 67.0%), so that prediction failed too. 30 questions added +32 points, the third replication. Pooled over three rule sets, a function's first question is worth about +20 points of edge-case accuracy, and a function nobody asks about gains nothing. See `gate5/RESULTS.md`.
