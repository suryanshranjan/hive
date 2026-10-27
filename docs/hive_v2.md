# Hive v2: the referee is the limit

Oct 27, 2026 · @Sumora

## Summary

Hive's limit is not how many agents can work without talking. It is how fast the swarm can tell right from wrong, and that capacity has to grow with the swarm.

What changed since v1:

- Collisions are cheap and rare. Measured in a real 16-agent swarm: 5% of concurrent pairs touch the same lines, and each collision costs a quarter of a restart. v1's coupling formula was 100× off and its restart assumption was wrong.
- A single merge gate, not coupling, is the first ceiling. Spreading checks across agents removes it; with trace-back, live bugs on main settle at f(1−s)/s whatever the swarm size.
- Gate 0 passed. Replaying the compiler's 3,947 commits against 620 tests the agents never saw, main was red 98% of the time but live regressions averaged 5 and never accumulated. Caught regressions died in 0.3 h; the 17% the swarm could not see lived about a day and a half.
- The deepest limits are the referee's: tests are consumed by adaptive use (√(k/n)), no automatic check covers arbitrary intent (Rice), and the swarm cannot exceed the rate at which intent enters it.
- Hive v2 therefore builds the referee as the product: sampled checks with trace-back, a hidden Ladder-gated suite, breakers as a quarter of the swarm, shapers scored on κ·d, and an interface that turns human answers into tests.

Gate 1, with 34 real Claude workers in six swarms, added two corrections. Agents did not game the tests, and at this project size each worker's onboarding (about 101k tokens) dwarfed both coordination and the work itself. Long-lived workers matter more than any coordination scheme until projects are large enough to give each worker many tasks.

The one-line law:

```latex
X_{useful} = \min\left( \frac{N(1-f)}{1+\kappa d (N-1)},\ \frac{1-f}{t_g},\ \frac{I}{b} \right)
```

Verdict: build the 10-to-100-agent system now with the v2 design. Do not claim 1,000 until Gate 2 passes. Odds that the gates pass through 100 agents: about 50%.

## Gate 0: the compiler's history replayed against a hidden suite

Main was never reliably green, and the swarm shipped anyway. Over 14 days and 3,947 commits, the compiler failed at least one of 620 hidden tests in 98% of 197 sampled commits, yet live regressions averaged 5 (0.8%) and did not accumulate. The final commit passes all 620.

&#91;embedded content: Replay of 197 sampled commits (every 20th) of anthropics/claudes-c-compiler, built and run against 620 hidden tests, Oct 27 2026\]

Live regressions stay small because most are caught within one task; the plateau at days 4 to 6 is the population the swarm's own tests could not see.

| Measure | Value | Basis |
| --- | --- | --- |
| Hidden tests | 620: [c-testsuite](https://github.com/c-testsuite/c-testsuite) 220 + 400 GCC torture execute tests | agents never saw either |
| Pass rate, first to last day | 23% → 100% | 141 to 620 passing |
| Regression events | 41 in 3,947 commits, f ≈ 0.010 per commit, ≈ 0.02 per task | coarse pass |
| Tests broken per event | median 1, tail to 40 | 32 events in fine windows |
| Lifetime, caught regressions (83%) | median 5 commits = 0.3 h, mean 0.6 h | 218 consecutive commits in 5 fine windows |
| Lifetime, unseen regressions (17%) | 7 to 142 h, median 31 h | 35 test-regressions, coarse pass |
| Live regressions | mean 5.0, max 46, red in 98% of samples | Little's law gives 4.6 |

What it confirms: a swarm with sampled checks runs with a small, steady number of unfound bugs on main, as the law predicts, and that was good enough to build a compiler that boots Linux. What it adds to the law: lifetimes are bimodal. Regressions the visible suite can see die in minutes; the rest live about a day and a half and are only found by accident. At 16 agents that tail held about one live unseen bug. At 1,000 agents, landings rise 60× and so does that tail unless detection speeds up, which is what breakers are for.

What it cannot test: how any of this changes with N, since the run had 16 agents throughout. The fast-lifetime figure is consistent with each agent running a 10% sample of a suite where a typical regression breaks several tests, but that is a consistency check, not a measurement of s.

## Gate 1, small version: real agents, Oct 27 2026

The first real-agent test of the law found no test gaming, poor scaling from 2 to 6 agents, and breakers that mostly widened the scope. Silent Claude workers built a SQLite-compatible engine in Python from a 140-line skeleton. They coordinated only through lock files in git and checked a 30% sample of the visible suite before landing. Python's sqlite3 was the referee for every test. One run per arm, so no error bars.

| Arm | Agents | Tokens | Minutes to 169 / 210 visible | Hidden template tests | Hidden combined queries | Breaker-found tests (58) | Landings with a rebase conflict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pilot | 2 builders | 240k | 5.3 / not reached (task cap) | 80% at stop | not run at stop | not run | 2 of 8 |
| A (v1) | 6 builders | 686k | 4.2 / 4.8 | 700/700 | 599/600 | 4 | 12 of 12 |
| B (v2) | 4 builders + 2 breakers | 1.2M | 6.5 / 6.8 | 700/700 | 600/600 | 15 | 8 of 24 |

**No gaming.** Visible and hidden pass rates matched within one point at every commit of all three runs, and no commit ever broke a passing test. When the visible tests sample the same distribution as the intent, honest agents generalise; the √(k/n) bound is a worst case they never approached.

**Tripling the builders bought 1.26×.** Time to 169 tests fell from 5.3 to 4.2 minutes while tokens per passing test rose from about 1.4k to 3.3k, an efficiency near 42%. Three causes are visible in the history:

- Arm A sat at 9/210 for its first 1.5 minutes, because every feature waited on the expression parser. With about 14 tasks on a chain about 4 deep, the span limit predicts N ≈ 1.5 · 14 / 4 ≈ 5. Here the critical path bound first, not coupling or the referee.
- Work was duplicated: two identical function-call parsers merged silently, and a WHERE grammar was abandoned after another worker's parser already covered it.
- Conflicts per landing rose from 0.25 at N = 2 to 1.0 at N = 6, consistent with κ(N−1) and a file-level κ near 0.25, the same as the C compiler. Each took 10 seconds to 2 minutes.

**Breakers found one in-scope bug class and then widened the scope.** Within the spec, only one bug escaped the builders: a type rule in comparisons, caught by Arm B and missed by A (599 vs 600). After that, over 40,000 random in-scope queries agreed with SQLite. The breakers' other finds were features outside the spec, such as CTEs, UNION, COLLATE and window functions, 58 root causes in all. Two breakers found bugs far faster than four builders fixed them, leaving 43 open. With a full reference implementation available, whoever writes tests ends up setting the intent.

Agents also shaped the code unprompted. They left hooks for each other (a GROUP BY hook, a scalar-function table, an outer-row parameter for subqueries). They also converged on one-line keyword additions so their merges stayed trivial.

### Foundation-first: prediction failed

Letting one agent build the shared core before six fan out made the swarm slower and costlier, not cheaper. The prediction, written before the runs, was about 2k tokens per passing test against 3.3k for fanning out at once.

| Run | Schedule | Tokens | Tokens per passing test | Minutes to 210 | Code conflicts | Hidden combined queries |
| --- | --- | --- | --- | --- | --- | --- |
| A | 6 fan out at once | 686k | 3.4k | 4.8 | 12 | 599/600 |
| A2 | 6 fan out at once (repeat) | 635k | 3.2k | 4.2 | 10 | 599/600 |
| F1 | founder, then 6 | 718k | 3.6k | 12.2 (founder 7.2) | 0 (6 lock races) | 599/600 |
| F2 | founder, then 6 | 713k | 3.5k | 13.1 (founder 8.4) | 0 | 564/600 |

Both founders built a plugin core, one file per feature. Code conflicts fell to zero, but conflicts had cost seconds each, so removing them saved almost nothing. The founder phase added 135k tokens and 7 to 8 minutes of serial time, and the six builders still took about 5 minutes after it. F2's lower score is entirely ABS(), which appears in no visible test: 35 of its 36 failures. The other swarms added ABS unprompted, so the combined-query suite partly tests beyond the spec.

**What actually sets the cost: onboarding.** Fitted on the first 14 builders, tokens per worker ≈ 101k + 4.9k × tasks landed. Without refitting, it predicted F1 and F2 within 12%. It under-predicted the breaker-arm builders by 1.48×, because their tasks were larger and their sessions three times longer. In every run, 84 to 93% of builder tokens went into getting started: reading the code, running the suite, learning the git routine. Coordination and collisions were a rounding error by comparison.

A protocol bug surfaced too: a claim written after a pull could overwrite another worker's lock without any git conflict. That caused six lock races in F1. Claims need a create-only check.

## Gate 2: a 10× project with 2, 6 and 12 long-lived workers, Oct 27 2026

The onboarding law held on a project ten times larger, while speed saturated near six workers and collisions grew far slower than predicted. All three swarms took the same engine from 362 to 1,340 passing tests across 99 open categories: functions, JSON, dates, window functions, set operations, CTEs, DML and DDL. They ran at the same time, and each finished the whole project.

| Swarm | Tokens | Minutes to all 1,340 | Speed vs 2 workers | Tokens per category | Conflicts per landing | Regressions on main | Hidden 2,260 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 workers | 515k | 17.7 | 1.0× | 5.2k | 0.14 | 0 | 2,260 |
| 6 workers | 963k | 8.2 | 2.2× | 9.7k | 0.33 | 0 | 2,260 |
| 12 workers | 1.62M | 7.8 | 2.3× | 16.4k | 0.48 | 1 (22 seconds) | 2,260 |

Scored against predictions written before launch:

- **Held: onboarding.** Predicted 697k, 1.10M and 1.71M tokens; observed 0.74 to 0.95 of that. Refitted, tokens ≈ 111k per worker + 3.0k per category, within 0.5% on all three swarms (two parameters, three points).
- **Held: no gaming.** Visible and hidden pass rates stayed within 0.4 points at every commit.
- **Failed: speed.** Twelve workers were 2.3× faster than two, not 3 to 4×. Going from six to twelve bought 5% more speed for 69% more tokens. The largest tasks (window functions, JSON, dates) took 6 to 7 minutes each, flooring the finish time.
- **Failed: collisions.** Predicted 0.15, 0.75 and 1.6 conflicts per landing; observed 0.14, 0.33 and 0.48, growing roughly as N^0.7. Workers put new features in their own modules unprompted.

The first semantic conflict appeared at N = 12. Three workers each wrote a helper with the same name, git merged them without complaint, and main lost 541 visible and 1,054 hidden tests. The author's pre-push check caught it, and the fix landed 22 seconds later. At N = 6, two workers built the same UPDATE features under different lock names, so claims should name test categories, not free text.

## What real swarms measured

Collisions between agents are rare and cheap. In the [C compiler repo](https://github.com/anthropics/claudes-c-compiler), 2,043 task leases were rebuilt from the lock files the 16 agents wrote to `current_tasks/`. Two tasks in flight at the same time touched the same file in 25% of pairs, the same function in 19%, and the same lines in 5%. The 426 source files behaved like about 4 regions, so v1's rule κ ≈ 1/m was off by about 100×.

| Measure | Value | How |
| --- | --- | --- |
| Concurrent pairs editing the same lines (κ) | 4.9% | 5,984 in-flight/landed pairs |
| Cost of one such collision | 4.9 to 9.4 min, central 7.1 | Regression on 1,595 tasks, day fixed effects |
| Same cost if a collision forced a restart | 25.9 min | Same regression on simulated restart durations |
| Collision cost as a share of a restart | 0.26 to 0.29 | Four cuts of the data |
| Herding onto hot spots | 1.1× random | Concurrent vs same-day random pairs |
| Median task length | 21 min (mean 36) | Lease open to lease close |
| κ, first week vs second | 6.5% → 3.0% | Agents split 36 hot files unprompted; phase confounded |

In [FastRender](https://github.com/wilsonzlin/fastrender), about 30,000 commits from up to 2,000 concurrent agents, build-fix commits were 2 to 3% of landings below 50 an hour and a flat 5 to 7% from 50 to 440 an hour. No cliff, but phase and rate are confounded.

Corrections to v1: the restart assumption is wrong; κ ≈ 1/m is wrong; FastRender ran about 2,000 agents at once in a hierarchy, not hundreds; [MacNet](https://arxiv.org/abs/2406.07155) ran over 1,000 talking agents in 2024, so "nobody has shown 1,000" holds only for silent swarms on real code.

## The law: seven limits, each deeper than the last

A swarm's useful output is the smaller of two things: what its machinery can land, and what its intent supply can specify.

```latex
X_{useful} = \min\left( X_{mech},\ \frac{I}{b} \right), \qquad X_{mech} = \min\left( \frac{N(1-f)}{1+\kappa d (N-1)},\ \frac{1-f}{t_g} \right)
```

N agents; κ share of concurrent pairs that edit the same lines; d cost of one collision in task lengths; f share of landings that carry a bug; t\_g full-suite run time in task lengths (only with a central gate); I bits of intent entering per hour; b bits needed per unit of correct work. Time is in mean task lengths.

| Limit | Rule | Status | Fixable? |
| --- | --- | --- | --- |
| 1 Coupling | efficiency = 1 / (1 + κ d (N−1)); halves at N ≈ 1 + 1/(κ d) | Form established (USL contention); constants ours | Yes: shapers cut κ |
| 2 Gate | one serial gate caps landings at (1−f)/t\_g whatever N is | Established queueing | Yes: each agent runs a random slice s of the suite |
| 3 Critical path | N ≤ W/D (Brent) | Established | No; schedule the longest chain first |
| 4 Threshold | bugs die out only if spread number R < 1; with checks spread across agents R is independent of N | Established branching-process threshold; the N-independence is our model | Yes: a fixed share of agents are breakers, so detection grows with N |
| 5 Referee consumption | k adaptive landings on n hidden tests leak √(k/n) error; a Ladder gate leaks (log(kn)/n)^(1/3) | Established ([Blum & Hardt](https://arxiv.org/pdf/1502.04585)) | Yes: replenish tests as fast as they are spent |
| 6 No universal referee | no automatic check decides a nontrivial semantic property of arbitrary programs (Rice) | Established | No: it draws the map of what Hive can build |
| 7 Intent bandwidth | value per hour ≤ I / b | Conjecture; MAST's largest failure class is specification at 42% | No: it is the product |

Two results are ours. With sampled checks and trace-back, live bugs on main settle at f(1−s)/s regardless of N, because more agents land more bugs but also run more checks, and the two cancel. Coupling and the gate combine as whichever is worse, not as resistors in parallel, because agents waiting at a gate are not editing.

Where the cliff sits when some bugs are invisible to the suite (coverage c, found after delay τ) and recovery reverts everything built on a bug: N\* ∝ (1−c)^−0.61 · τ^−1.04 · κ^−0.55, fitted on 8 runs and 1.4× typical error held out. Halving τ roughly doubles the reachable swarm; halving the unseen share buys about 1.5×.

A cost term the seven limits left out, measured in Gate 1 across 30 workers: each worker pays a fixed onboarding cost c\_on before its first useful change, about 101k tokens and 1.5 to 2 minutes here, against about 5k tokens per task after that.

```latex
\text{tokens per task} \approx c_{task} + c_{on}\,\frac{N}{T}
```

T is tasks completed. Overhead dominates until each worker does about c\_on / c\_task ≈ 20 tasks. A swarm whose workers exit after one task, as Hive v1's loop prescribes, spends roughly 95% of its tokens onboarding.

## Simulation evidence

A new simulator with only mechanics coded (`hive_sim.py`) was fitted on some configurations and tested on ones it had not seen. Three things in v1 failed; the replacements held.

| Experiment | Fitted on | Tested on | Result |
| --- | --- | --- | --- |
| A: v1 coupling law, κ = 1/m | even codebases | uneven codebases, 54 runs | Failed: R² −0.26 on log scale, worst 12× off |
| A: collision law 1/(1+κ d(N−1)) | even codebases, d = 0.3 | uneven codebases and new d, 90 runs | R² 0.92, 98% within 2×, constant 1.00 |
| B: one serial gate | none | N = 4 to 1,024 | throughput capped at 0.8 to 0.95 of 1/t\_g; batching helped only when bugs were rare |
| B: sampled checks, trace-back | none | N = 16 to 1,024, s = 0.5% to 30% | live bugs matched f(1−s)/s within 3%, flat in N |
| B: v1 fixed-delay referee | none | N = 16 to 1,024 | live bugs grew 60× over the range; with bounce recovery efficiency fell to 0 |
| C: combined law, no fitting | none | 80 random swarms | 99% within 2×; series form biased by 1.4× for gated swarms |
| C2: gate + coupling blend | 36 swarms | 60 fresh swarms | "whichever is worse" put 95% within 1.25× |
| D: unseen bugs, bounce recovery | 8 even-codebase runs | 12 uneven ones | one-constant formula failed (2.2× typical, 3.4× worst); power fit 1.37× typical, 1.8× worst |
| D: unseen bugs, trace-back | none | N = 8 to 1,024 | efficiency flat at 0.77; unseen bugs on main grew in proportion to N, matching landings · f · (1−c) · τ within 0.90 to 1.18× |

What the simulation cannot show: real agents, real code, or whether the sampled-check result survives tests that miss bugs. Under the restart rule the simulator halves efficiency at 1.4 agents per region, not v1's 2.9; that constant moves with the spread of task lengths, so neither number should be relied on.

## Hive v2 design: one change per limit

Workers still never talk. What changes is the referee, which becomes the swarm's main product.

1. **Shapers scored on κ·d from git.** The compiler's agents sat at about 0.01, which halves efficiency near 100 agents (range 60 to 330). Reaching 1,000 needs about 0.001.
2. **No central merge gate.** Each worker runs a random slice s of the suite on main plus its change, then lands. Any failing test is bisected to the change that broke it and only that change is reverted. To hold about L live bugs, s ≈ f/(L+f): with f = 20% and L = 1, s ≈ 17%.
3. **Critical path first.** The field weights pressure by how many tasks wait on a region, so the longest chain is always being worked.
4. **Builders and breakers.** About a quarter of the swarm hunts bugs: fuzzing, comparing against a reference such as the GCC oracle, and writing failing tests. Detection then grows with N by construction.
5. **Two suites.** A visible suite is the workers' signal. A hidden suite decides acceptance and reports only clear improvements (a Ladder rule). Breakers feed the hidden suite. Budget: a day of 1,000 agents is about 40,000 landings, needing about 180,000 hidden tests under the Ladder rule, or 16 million without it.
6. **Scope by checkability.** First targets have an external referee: a migration diffed against the old system, or a rebuild against test262, sqllogictest or the web-platform tests. Nothing without a checker.
7. **An intent interface.** The human is asked only the question that splits the most remaining ambiguity, and each answer becomes tests. Measure I directly: bits of specification per human hour.

Kept from v1: the five-step worker loop, leases that expire, evaporation of signals, escalation to stronger models, and steering by editing the world.

Changed after Gate 1: workers are long-lived and take task after task, because onboarding costs about 20 tasks' worth of tokens. Context packs are judged by onboarding tokens. Claims are create-only. No founder phase; the swarm shapes its own extension points within minutes anyway.

## Build plan, odds and kill conditions

Build the 10-to-100-agent system now with the v2 design; the 1,000-agent claim waits for Gate 2. Each gate is a prediction that can fail.

| Gate | Setup | Cost | Prediction if the law holds | Kills |
| --- | --- | --- | --- | --- |
| 0 Replay | compiler history vs hidden suite | 1 machine-day | small steady live-bug count, bimodal lifetimes | passed Oct 27 2026 |
| 1 Half-hidden suite | 10 agents, SQL engine vs sqllogictest, half the tests hidden; one arm with a human answering spec questions | 1 day, a few hundred dollars | visible-minus-hidden pass gap grows about as √(landings); the spec-answer arm lands more correct work | small version ran Oct 27 2026: gap flat in 3 runs, so gaming is not binding at this scale; the spec-answer arm is still to run |
| 2 Breakers | 30 vs 100 agents, with and without a 25% breaker share | 2 to 4 days | unseen-bug lifetime falls from about 35 h toward hours; efficiency at 100 stays above half of efficiency at 30 | efficiency halves → an unmodelled limit; 1,000 is off the table |
| 3 Scale | 300 agents, then 1,000 | weeks, up to $1.25M per two weeks | still rising past 300 as measured κ·d falls | peak below 300 |

Odds, honest and rough:

- Collisions cost about a quarter of a restart in other projects too: 60%.
- Live bugs stay flat from 10 to 100 agents with sampled checks and trace-back: 55% (Gate 0 raised this from 50%).
- The referee, not coupling, is the binding limit at 1,000: 65% (down from 70%: no gaming seen in Gate 1; for small projects the critical path bound first).
- Breakers remove the unseen-bug cliff on real code: 40%.
- Hive at 1,000 agents producing value a buyer pays for within a year: 15%.

Cheapest next experiment: a project about 10× larger, so each worker can do 10 to 20 tasks, run with 2, 6 and 12 long-lived workers. Prediction: tokens per task fall toward 5k + 101k/(tasks per worker), and the coupling and referee terms finally become visible above onboarding. Foundation-first was tested on Oct 27 2026 and failed.

Open questions: whether κ·d can be estimated from a dependency graph before a run; what half-life signals and memories should have; which interface changes shapers may make alone.

## Sources

- [Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler), Anthropic, Feb 2026, and the [repository](https://github.com/anthropics/claudes-c-compiler)
- [FastRender repository](https://github.com/wilsonzlin/fastrender) and [Simon Willison's write-up](https://simonwillison.net/2026/Jan/23/fastrender/), Jan 2026
- [c-testsuite](https://github.com/c-testsuite/c-testsuite) and [GCC torture tests](https://github.com/gcc-mirror/gcc), the hidden suites
- [Concurrency control performance modeling](https://web.eecs.umich.edu/~jag/eecs584/papers/acl.pdf), Agrawal, Carey, Livny, 1987
- [A general theory of computational scalability](https://ar5iv.arxiv.org/html/0808.1431), Gunther
- [The Ladder: a reliable leaderboard](https://arxiv.org/pdf/1502.04585), Blum and Hardt, 2015, and [the reusable holdout](https://www.research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/), Google, 2015
- [Why do multi-agent LLM systems fail?](https://arxiv.org/html/2503.13657v2), UC Berkeley, 2025
- [The merge queue is the new bottleneck](https://tianpan.co/blog/2026-07-02-the-merge-queue-is-the-new-bottleneck), Jul 2026, and [Mergify on agents](https://mergify.com/blog/merge-queues-and-ai-coding-agents)
- [Flake-aware culprit finding](https://research.google/pubs/flake-aware-culprit-finding/), Google, 2023; [Risk-aware batch testing](https://arxiv.org/abs/2604.00222), Mozilla, 2026
- [Scaling LLM-based multi-agent collaboration (MacNet)](https://arxiv.org/abs/2406.07155), 2024; [SwarmWorld](https://arxiv.org/html/2608.26081), MIT, Aug 2026
- Hive v1 sources: Google Research on scaling agent systems, Cursor on long-running agents, pressure-field coordination, CodeCRDT, Codebolt StigmergySwarm

Code: `hive_sim.py`, `expA.py` to `expD.py`, `ccc_*.py`, `replay.sh`, `analyze.py`, `analyze_fine.py`, shared in the chat.
