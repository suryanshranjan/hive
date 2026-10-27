# Hive

**Silent swarms of AI coding agents that build software to the owner's intent.**

Hive runs many coding agents on one repository. They never message each other: they coordinate only through git, claiming areas of work and landing changes through a guard that refuses anything that breaks a passing test. The owner's intent reaches them as tests: worked examples from the owner, answers to the builders' questions, and the company's documents.

This repository holds the research behind it (24 pre-registered experiments, about 30 swarms, every failure reported) and the first version of the tool.

**Start with [`BRAIN.md`](BRAIN.md):** what is known, how sure we are, every prediction and whether it held.

## The main finding

Silent swarms finish what they are given. On rules no model can guess, they are limited by intent: how much of what the owner wants reaches them.

- **Questions help, but hit a floor.** Builders ask about what they can imagine. About a fifth of errors survive any number of questions, because they sit at decisions nobody thinks to ask about ([Gate 12](gates/gate12/RESULTS.md)).
- **When the owner points, intent gets through.** One worked example per rule, chosen by the owner, beat the same number of answers to builder-chosen questions: 89.4% against 67.2% of hidden tests ([Gate 13](gates/gate13/RESULTS.md)).
- **With both, swarms reach 95–98%.** Owner examples plus about 17 questions: 95.2% and 98.2% on two rule sets ([Gates 13](gates/gate13/RESULTS.md), [17](gates/gate17/RESULTS.md)), and **95.0% end to end at 6 workers with no broken commits** ([Gate 24](gates/gate24/RESULTS.md)).
- **On a real company's rules: 84.8%,** against 49.6% before, using the founder's own examples, questions and the company's documents ([Gate 20](gates/gate20/RESULTS.md)). The documents covered 2 of 10 functions; the rest lived only in the founder's head.

The worked examples are **Specification by Example**, an established practice. What this work adds is measurement: a randomized comparison of owner-chosen examples against builder questions, and the question floor. See [`docs/related_work.md`](docs/related_work.md) for what is and is not new.

## What the evidence says

| Finding | Result | Where |
| --- | --- | --- |
| Silent swarms finish the project and do not game the tests | Every project finished; visible and hidden pass rates within 0.4 points | Gates 1–3 |
| Collisions between agents are rare and cheap | 5% of concurrent pairs touch the same lines; about a quarter of a restart each | C compiler history |
| Cost is mostly onboarding | About 110k tokens per worker to start, 3k–5k per task after | Gates 1–3 |
| On a small machine, speed is set by CPU per guard check | 3.5 min on 24 cores, 12.1 on 4; caching main's results saves about a fifth | Gates 10, 21, 22 |
| Without the owner's intent, swarms pass every visible example but few hidden tests | 24–58% hidden | Gates 3–24 |
| Questions cause the gain, with diminishing returns | +25 to +32 points from 30 questions on five rule sets | Gates 3–8, 11 |
| Owner-chosen examples beat builder-chosen questions | 2.7× the errors fixed (agent rules); 1.17× (a real founder) | Gates 13, 20 |
| The whole design works as a system | 95.0% hidden at 6 workers, no breaking commit on main | Gate 24 |

**Failed and withdrawn, with the evidence kept:** asking in blocks of 3 per function, a one-constant law for questions, contrast examples, coverage-planned and defaults-first questions, largest-first claiming, a two-term speed model. Each was predicted, tested and dropped ([`BRAIN.md`](BRAIN.md) §6).

## Hive v1 (in progress)

The tool packages the measured design for any repository with tests. Plan and milestones: [`docs/hive_v1_plan.md`](docs/hive_v1_plan.md).

| Milestone | Status |
| --- | --- |
| M1 Guard for any test runner (JUnit XML), cache keyed by code content, secrets refused | **Done**: pytest (`tests/test_guard.sh`) and a real company's Node.js backend (384 tests) |
| M2 Claims on areas of the codebase | **Done** (`tests/test_claims.sh`) |
| M3 `hive run`: headless workers, one clone each | **Done** (`tests/test_run.sh`; a real 2-worker run, $0.43) |
| M4 Owner session: examples and live answers become tests | Planned |
| M5 First real feature, built end to end, scored on the owner's held-back tests | Planned |

```
python -m hive init --test-cmd "python -m pytest -q --junitxml=.hive/junit.xml"
python -m hive land <short_name> "<what you did>"
```

Run workers in a container or throwaway VM: they execute shell commands.

## How this research works

Every experiment (a "gate") registers its predictions and kill conditions on GitHub **before** it runs (`lab/run_gate.py` refuses to start otherwise), then scores them in its `RESULTS.md`, failures included. Hidden test suites are never committed; they regenerate from fixed seeds. Lab flaws found later are written up, not hidden ([`gates/LAB_NOTE_guard_python.md`](gates/LAB_NOTE_guard_python.md)).

## Layout

| Path | Contents |
| --- | --- |
| [`BRAIN.md`](BRAIN.md) | Shared memory: the law and its status, measured constants, evidence log, prediction scorecard, design, open questions |
| [`hive/`](hive/) | Hive v1, the tool |
| [`gates/`](gates/) | Every experiment: predictions, results, referee code, swarm histories (`*.bundle`), logs. Gates 0–24 |
| [`lab/`](lab/) | Run any gate in one command; [`lab/QUEUE.md`](lab/QUEUE.md) is the queue and session handoff |
| [`docs/`](docs/) | Design write-ups, the v1 build plan, related work |
| `real_repos/`, `sim/` | Analysis of real agent-swarm histories (Anthropic's C compiler); the simulator |
| `tests/` | Tests for the tool |

## Reproducing

Run swarms in a container (the lab used `node:22-bookworm` with Python, git, SQLite and Claude Code; see [`lab/README.md`](lab/README.md)).

```
python3 lab/run_gate.py lab/experiments/<config>.json            # a whole intent gate, after its predictions are pushed
python3 gates/gate2/referee/gen2.py hidden2 5000000 20            # Gate 2's hidden suite (use SQLite 3.49; see gates/gate10/RESULTS.md)
python3 gates/gate1/referee/evaluate.py <swarm clone> hidden_big out.json
```

Every swarm's full history is in its gate's `swarms/*.bundle` (`git clone gates/gate24/swarms/V1.bundle`).

## Privacy

Gates 7, 18 and 20 used a real company's rules (Company X). Its name, rules, examples, documents and answers are not in this repository; those gates publish aggregate numbers only.
