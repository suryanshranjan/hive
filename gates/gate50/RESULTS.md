# Gate 50 results: does the swarm beat one agent? Oct 30 2026

**Question.** With today's fast model, is a swarm still faster than one agent, and at what cost? Hive's premise rested on runs with an older model; one builder alone had never been measured.

**Answer.**
- **Yes. The swarm buys speed with money, up to about 7 builders.** On the deep project (from a 221-line skeleton to 1,340 tests):

| Builders | Time to 95% | Speed vs one | Cost | Cost vs one | Hidden | Breaks of main |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 12.8 min | 1.00× | $2.94 | 1.0× | 99.8% | 0 |
| 2 | 11.0 min | 1.16× | $4.72 | 1.6× | 100% | 0 |
| 4 | 6.2 min | 2.05× | $5.61 | 1.9× | 99.8% | 0 |
| **7** | **4.2 min** | **3.03×** | $5.53 | 1.9× | 100% | 0 |
| 12 | 6.6 min | 1.93× | $9.98 | 3.4× | 99.8% | 0 |

- **One builder alone finished the whole engine in 12.8 minutes for $2.94.** It is the cheapest way, and it was as correct as any team. Seven builders were three times faster for about twice the money. Twelve were slower than seven and cost 3.4 times one.
- **The scalability fit:** serial share σ = 0.25 (the foundation everything waits on), crosstalk κ = 0.013, peak near 7.6 builders. The crosstalk equals the law's coupling constant κd = 0.013, measured on the C compiler's history a week ago.
- **What the law got wrong:** "about one CPU core per builder". On this 2-core machine that rule picks 2 builders, which were only 1.16× faster than one. A builder keeps a core busy only while its agent works or its tests run, and here the full suite takes 1.4 seconds. The law now counts that share (see below).

## Setup

- **Project:** Gate 46's deep project, from 9 of 1,340 visible tests to all of them, in 127 categories. Protocol v2. Hidden suite: gen2.py, seed 5000000, private, Gate 46's left-out categories (2,200 scored).
- **Teams:** flat and silent (Gate 46's prompt, time cap raised to 90 minutes). Teams of 1, 2, 4, 7 and 12, each alone on the 2-CPU machine, in a shuffled order (N4, N1, N12, N2, N7). One run each. Predictions pushed before any team ran (`3b7e3a0`).
- Gate 46's two flat teams of 7 took 4.4 and 6.3 minutes. That spread is the noise: one run per size cannot separate differences under about 30%.

## Predictions scored (registered code: `referee/analyze.py`; output in `results/analysis.txt`)

| # | Prediction | Result |
| --- | --- | --- |
| E1 | One builder reaches 95% within 90 minutes | **Held:** 12.8 min |
| E2 | Seven builders ≥ 2× faster than one | **Held:** 3.03× |
| E3 | Twelve not > 10% faster than seven | **Held:** twelve were slower (6.6 vs 4.2 min) |
| E4 | Seven cost ≤ 1.5× one | **Failed:** 1.88× |
| E5 | Hidden within 1 point | **Held:** 99.8–100% |
| Rule | S(7) < 1.25: the swarm barely beats one agent | **Did not fire** |
| Rule | E3 held and the peak is ≤ 7: the guard's CPU binds | **Read with care.** The peak is 7.6, but the guard's suite takes 1.4 s, so the guard is not what binds. Twelve agent processes on 2 cores, plus the serial foundation, are the likelier limits. Gate 51 measures the machine's load to separate them. |

## What it means

1. **The swarm is a speed-for-money trade.** Twice the money buys about three times the speed, up to about 7 builders. That is a choice for the owner, not a fact to hide. One builder is the cheap option, and it was just as correct.
2. **The law's hardware term was from an older world.** In Gate 21 the old model and a slow suite kept a core busy per builder. With a fast model and a 1.4-second suite, two cores carried seven builders. The binding limits are now the serial foundation (σ = 0.25) and crosstalk (κ = 0.013), as the scalability fit shows.
3. **The single builder did something no team did:** it fuzzed its engine against Python's own `sqlite3` and fixed what it found. The prompt allowed that for this project. Teams spent their time landing categories instead. Correctness ended the same.

## Turned into the product (this commit)

- **`hive/law.py`:**
  - A builder's CPU share is now its agent plus its test runs, at most a core each, replacing one core per builder. On a 2-core laptop with fast tests, the law now picks up to 8 builders, not 2.
  - The coupling limit is the peak of Gate 50's scalability fit.
  - New: `speedup(n)`, `cost_vs_one(n)` and `trade(n)`.
- **`hive start`** tells the owner the trade in plain words: "I'll put 7 builders on it (…): about 2.3× the speed of one builder, for about 1.9× the cost." Speeds are the fit's, costs Gate 50's measurements.
- Tests: the CPU term with slow and fast suites, the fit's peak, the trade sentence. All Python suites and 7 of 8 shell suites pass. `test_cloud.sh` has 2 failures (expired-AWS-credential cases) that occur identically without this change.

## Limits

- One run per team size, one project, 2 CPUs. The fit is to five noisy points: it predicts 2.3× at 7 where 3.0× was measured.
- Costs are at list price with the session's default model.

## Files

`prompts/` (prompt, predictions), `referee/` (driver, analysis), `results/` (analysis, per-team progress after every landing, worker costs, run log), `swarms/` (all five teams' histories), `logs/`.
