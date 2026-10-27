# Hive

Research on swarms of AI coding agents that coordinate only through a shared repository, never by messaging. This repo holds the code, data and swarm histories behind **Hive v2: the referee is the limit** ([doc](https://claude.ai/artifact/PZKUKvJY6a7C3dG8ZJrT8H)). The original Hive v1 write-up is in `docs/hive_v1.md`.

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
| `gate2/` | Prepared, not yet run: 113-category project, seed repo bundle, long-lived worker prompt, `PREDICTIONS.md` registered before launch |

## Reproducing

Hidden test suites are deliberately not committed, so future agents working in this repo can't read them. Regenerate them from the fixed seeds:

```
python3 gate1/referee/gen.py hidden_big 9000 50        # 700 template tests
python3 gate1/referee/fuzz.py hidden_fuzz 77000 600    # 600 combined queries
python3 gate2/referee/gen2.py hidden2 5000000 20       # 2,260 Gate 2 tests
python3 gate1/referee/evaluate.py <swarm repo or bundle clone> hidden_big out.json hidden_fuzz
```

Gate 0 needs `anthropics/claudes-c-compiler`, `c-testsuite/c-testsuite`, and the GCC torture tests (`gcc/testsuite/gcc.c-torture/execute`); see `gate0/replay.sh`.

## Next experiment (Gate 2)

2, 6 and 12 long-lived workers on a project with about 100 open tasks, 60 minutes each, run concurrently. It tests whether tokens per task follow `c_task + c_on * N / T` and whether collisions and the referee become visible once onboarding stops dominating. Predictions are in `gate2/prompts/PREDICTIONS.md`.
