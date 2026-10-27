# Hive v1: build plan (Oct 28 2026)

Hive v1 packages what Gates 1 to 24 measured into a tool that runs on any repository with tests. Design source: `BRAIN.md` §7 and `gates/gate24/RESULTS.md` (the end-to-end test: 95.0% hidden at 6 workers, no breaking commits).

## What v1 is

| Part | Measured design | Evidence |
| --- | --- | --- |
| Swarm | Silent workers, one clone each, coordinating only through git | Gates 1–3, 24 |
| Claims | A worker locks an area (a group of tests) before working on it; overlapping claims are refused | Gate 3 |
| Guard | Before a push: no new duplicate definitions, and no test that passes on main may fail; main's results cached by code content | Gates 3, 21–23 |
| Intent | The owner's worked examples (one per rule they know) as tests, generated suggestions to confirm, the company's documents, then builder questions; every answer becomes a test | Gates 13–20 |
| Machine | About one core per worker, in a container | Gates 10, 21 |

## What changes from the lab

The lab tools assume one project (a SQL engine with JSON test files run by its own `run_tests.py`). v1 must work on a real repository:

1. **Any test runner.** The guard reads per-test results as JUnit XML, which pytest, jest, vitest, go test (via gotestsum), JUnit and others emit. The project declares its command in `.hive/config.json`.
2. **Any areas.** Claims name areas defined in the config (test file globs or test-name prefixes), not the lab's JSON categories.
3. **A real owner.** Questions go to a person in a terminal (or come from documents and examples), not to an encoded oracle. Every answer becomes a test in the project's own framework.
4. **One command.** `hive` instead of the lab's scripts.

## Layout

```
hive/                      the package (Python 3.11+, standard library only)
  __main__.py              CLI: hive init | claim | land | run | owner | status
  config.py                .hive/config.json: test command, JUnit path, areas, workers
  junit.py                 per-test results from JUnit XML
  guard.py                 the content-keyed cached guard, runner-agnostic (from gates/gate23/tools/land.py)
  claims.py                area claims through lock files (from gates/gate3/tools/claim.py)
  swarm.py                 clones, prompts, headless workers, cost log (from lab/make_swarm.py, lab/launch.py)
  owner.py                 owner session: examples → tests, live answers → tests, question log
  templates/worker.md      the builder prompt (from lab/templates/prompt_builder.md)
tests/                     Hive's own tests
```

## Milestones

| # | Milestone | Done when |
| --- | --- | --- |
| M1 | Runner-agnostic guard | **Done.** `tests/test_guard.sh` (pytest, 7 checks) and a real company's Node.js backend (private; `node:test` with Node's JUnit reporter, 384 tests): clean change lands, regression refused, duplicate refused, cache hit after a lock commit, secrets refused, artifacts left out, any shared branch name |
| M2 | Claims on areas | **Done.** `tests/test_claims.sh` (9 checks, repeated 4 times): overlapping claims refused, unknown areas refused, two simultaneous claims leave exactly one holder, landing frees the area |
| M3 | `hive run` | **Done.** `tests/test_run.sh` (fake workers, 6 checks: result passes, both land, no lock left, source untouched, cost logged). Real check: 2 Claude workers built a two-area goal in 0.5 min for $0.43; one lost a simultaneous claim, withdrew automatically and took the other area; 17/17 tests, 15 of them added by the workers |
| M4 | Owner session | **Done.** `hive run --examples --questions`, `hive owner`, `hive ask`, `hive answers`. `tests/test_owner.sh` (6 checks): examples in every prompt, question reaches the owner's terminal and the answer comes back, response time recorded, budget enforced, the answer lands as a passing test |
| M5 | First real feature | **Run (Gate 25):** 23/23 hidden acceptance tests and 384/384 existing tests on a real company's backend, $3.18. The founder delegated 11 of 12 answers to an AI proxy, so the founder-live version is still to run |

M1 to M4 use small sample repositories so they cost little. M5 is the breakthrough test.

## M5 success criteria (registered before the run, as for every gate)

- At least 95% of the owner's held-back acceptance tests pass, with no code review by the owner.
- No commit on main breaks a passing test that stays broken.
- Owner time: examples plus live answers, logged.
- Every failure reported.

## Privacy

A real company's code, rules, examples and answers never enter this repository. Hive runs on the company's own repository inside a local container; only aggregate numbers are published, as in Gates 7, 18 and 20.
