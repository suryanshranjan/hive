# Hive brain

Read this first. It is the shared memory for anyone working on Hive, human or agent: what we know, how sure we are, what is being tested, and exactly how to continue. When you learn something, update this file in the same commit as the evidence.

Last updated: Oct 27 2026, 14:00 IST.

## 1. The question

Can a swarm of AI coding agents that never message each other build real software by coordinating only through a shared git repository? And what limits how big and how correct such a swarm can get?

## 2. Current answer

On projects up to 1,340 tests and 12 agents: yes. Silent swarms finished every project they were given. They never gamed the tests, and collisions were rare and cheap.

Two things limit them today:

- **Cost is mostly onboarding.** Each worker spends about 110k tokens getting started, against about 3k to 5k per task after that.
- **Speed stops improving at around 6 to 12 workers.** The biggest task, and how late it gets claimed, sets the finish time.

The deeper limit, still to be measured, is intent: a swarm can only be as right as its ability to tell right from wrong, and that knowledge has to come from somewhere. Gate 3 step 3 tests this and is ready to run.

## 3. The law and how sure we are of each part

```
X_useful = min( N(1−f) / (1 + κ·d·(N−1)),   (1−f) / t_g,   I / b )
```

N agents; κ share of concurrent pairs that edit the same lines; d cost of one collision, in task lengths; f share of landings that carry a bug; t_g full-suite time of a central gate; I bits of intent entering per hour; b bits needed per unit of correct work.

Status tags: **established** means outside theory or our data on real agents; **model** means our formula, fitted on some cases and checked on held-out ones; **conjecture** means not yet tested.

| Limit | Rule | Status |
| --- | --- | --- |
| 1 Coupling | efficiency = 1/(1 + κd(N−1)) | Form established (USL contention); constants measured on one real project |
| 2 Gate | a serial gate caps landings at (1−f)/t_g | Established (queueing) |
| 3 Critical path | N ≤ W/D (Brent) | Established; seen binding in Gate 1 |
| 4 Threshold | bugs die out only if R < 1; with sampled checks and trace-back, live bugs = f(1−s)/s, independent of N | Branching threshold established; the N-independence is our model, matched in simulation within 3% |
| 5 Referee consumption | k adaptive landings on n hidden tests leak √(k/n); a Ladder gate leaks (log(kn)/n)^(1/3) | Established (Blum & Hardt 2015); not binding at our scale |
| 6 No universal referee | no automatic check decides arbitrary intent | Established (Rice) |
| 7 Intent bandwidth | useful work per hour ≤ I/b | **Conjecture**; Gate 3 step 3 tests it |
| Onboarding | tokens ≈ c_on·N + c_task·T | **Model**, held out three times (Gates 1, 2, 3) |
| Tail | finish ≥ max(work/N, longest task + when it starts) | Established (scheduling theory); seen binding in Gate 3 |
| Coverage cliff | N* ∝ (1−c)^−0.61 · τ^−1.04 · κ^−0.55 | Model, simulation only (1.4× typical error held out) |

## 4. Measured constants

| Constant | Value | Where |
| --- | --- | --- |
| κ, same lines | 4.9% of concurrent pairs | C compiler, 2,043 task leases |
| κ, same file | 25% | C compiler |
| d | 0.26 to 0.29 of a restart (about 7 min against a 26 min restart) | C compiler |
| f | 0.010 per commit, about 0.02 per task | Gate 0 |
| Live bugs on main | mean 5 of 620 hidden tests, steady, never accumulating | Gate 0 |
| Bug lifetimes | bimodal: 83% caught in about 0.3 h, 17% live 7 to 142 h (median 31 h) | Gate 0 |
| c_on, onboarding | 101k (Gate 1), 111k (Gates 2 and 3) tokens per worker | Gates 1 to 3 |
| c_task | 4.9k per task (Gate 1), 3.0k per category (Gate 2) | Gates 1, 2 |
| Conflicts per landing | 0.14 / 0.33 / 0.48 at N = 2 / 6 / 12 (about N^0.7); 0.36 at 8 and 0.44 at 12 with category claims | Gates 2, 3 |
| Cost of one conflict | 10 s to 2 min | Gates 1 to 3 |
| Visible minus hidden gap | under 1 point at every commit, every swarm | Gates 1, 2, 3 |

## 5. Evidence log

| Gate | Date | What ran | Result |
| --- | --- | --- | --- |
| Real repos | Oct 27 | C compiler history (16 agents), FastRender (up to 2,000 agents) | Collisions rare and cheap; v1's κ ≈ 1/m was 10× off; no cliff in FastRender's build-fix rate |
| Simulation | Oct 27 | `sim/hive_sim.py`, experiments A to D, fitted then held out | Sampled checks with trace-back hold live bugs flat in N; v1's fixed-delay referee fails |
| Gate 0 | Oct 27 | Compiler history replayed against 620 hidden tests | Small steady live-bug count; bimodal lifetimes |
| Gate 1 | Oct 27 | 34 Claude workers, 6 swarms, SQL engine with SQLite as referee | No gaming; 2→6 builders bought 1.26×; onboarding dominates; foundation-first failed |
| Gate 2 | Oct 27 | 10× project, 2 / 6 / 12 long-lived workers | Onboarding law held; speed saturated near 6; collisions grew slower than predicted; first semantic conflict, repaired in 22 s |
| Gate 3, step 2 | Oct 27 | Protocol v2 (category claims, guarded landing), 8 and 12 workers | Onboarding law held a third time; guard blocked both would-be regressions; all 2,960 hidden tests pass; no gaming (gap ≤ 0.4 pts); finish time set by the tail |
| Gate 3, step 3 | not yet run | Intent test: invented business rules, 0 / 30 / unlimited questions to a product owner | Built and reset; two attempts stopped at 3 minutes (usage limit, user stop) |

## 6. Prediction scorecard

All predictions are written down before the run, in each gate's `PREDICTIONS.md`.

- **Held:** onboarding law (Gates 2, 3); no gaming (Gates 1, 2, 3); guard keeps regressions off the tip of main (Gate 3; the blocked commit still sits in history next to its fix, so `--continue` should squash); no overlapping claims (Gate 3).
- **Failed:** foundation-first is cheaper (Gate 1); speed of 3 to 4× at 12 workers (Gate 2: 2.3×); collisions growing as κ(N−1) (Gate 2: slower); finer claims lowering the time floor (Gate 3: 8.7 min against 7.8).
- **Untested:** 24 workers; intent bandwidth; breakers at scale.

## 7. Design as of now (Hive v2 plus protocol v2)

- Workers never talk. Long-lived workers take task after task, because onboarding costs about 20 tasks' worth of tokens.
- Claims name test categories (`gate3/tools/claim.py`); overlapping claims are refused and races resolved by commit order.
- Landing is guarded (`gate3/tools/land.py`): no new duplicate definitions, and no test that passes on main may fail after the change.
- Two suites: visible tests guide the workers, hidden tests judge. Hidden suites are never committed.
- No founder phase: the swarm shapes its own extension points within minutes.
- **Next changes:**
  - Claim the largest unclaimed category first, which cuts the tail.
  - Modules register themselves, which removes most conflicts.
  - `land.py --continue` squashes the fix into the blocked commit, so every commit on main passes.

## 8. Open questions, most important first

1. **Intent bandwidth.** On rules a model cannot guess, how much does access to a product owner raise correctness, and how many questions is it worth? (Gate 3 step 3, ready.)
2. **The tail.** Does largest-first claiming bring 12 workers under 7 minutes?
3. **The largest swarm this lab allows**: 20 workers with largest-first claiming.
4. **Turning intent into tests automatically**: the referee as the product.
5. **Breakers at scale**: do they shorten the 31-hour unseen-bug lifetime?

## 9. Next experiments, exactly

1. **Intent test** (about 1.4M tokens, 45 minutes). Launch the 9 workers with the prompts in `gate3/prompts/`. They have to be regenerated from `prompt_intent.md` per worker; the rendered copies sit in the working machine at `gate3/p_Q*-w*.md`. Then unseal the oracle, regenerate the hidden suite and score with `gate1/referee/evaluate.py`. Score against I1 to I5 in `gate3/prompts/PREDICTIONS.md`, and check the cheating signature.
2. **Largest-first at 12 and 20 workers** (about 4M tokens). Same project as Gate 3 step 2. Registered prediction to write first: 12 workers under 7.0 minutes.
3. **Self-registering modules** at 12 workers: conflicts per landing below 0.2.

## 10. What this lab allows

- At most 20 agents at once per session. A launch beyond that silently starts only the first 20.
- A usage limit stops all agents mid-run. It hit after roughly 4M subagent tokens in one window. Plan runs to fit, and record partial runs as aborted.
- 2 CPUs. Every guarded landing runs the suite twice, so timings include CPU contention. Compare swarms only when they ran under the same load.
- The workspace container can restart: background servers die and must be restarted. Bare repos and files survive.
- Pushing to GitHub needs the claude.ai account linked to GitHub. Otherwise the work arrives as a git bundle that the user pushes.

## 11. How to continue

```
git clone https://github.com/suryanshranjan/hive && cd hive
cat BRAIN.md docs/hive_v2.md gate2/RESULTS.md gate3/RESULTS.md
# regenerate hidden suites (never commit them)
python3 gate1/referee/gen.py hidden_big 9000 50
python3 gate1/referee/fuzz.py hidden_fuzz 77000 600
python3 gate2/referee/gen2.py hidden2 5000000 20
# a swarm: clone a seed bundle into a bare repo, make one clone per worker,
# render one prompt per worker, launch the workers, then replay main:
python3 gate2/referee/evaluate.py <bare repo> hidden2 out.json hidden_big
```

Rules of the lab:

- Register predictions before launching.
- Change one thing per experiment.
- Every worker logs CLAIM, LAND, CONFLICT and BLOCKED events to `HIVE_LOG`.
- Hidden suites and private intent stay out of the repo until their test has run.
- Report failures as plainly as successes.

## 12. Changelog

- **Oct 27 2026:**
  - Hive v1 doc analysed; real-repo measurements; simulator v2; Hive v2 doc (`docs/hive_v2.md`).
  - Gates 0, 1 and 2 run.
  - Protocol v2 built.
  - Gate 3 scale step run (8 and 12 workers).
  - Gate 3 intent step built, attempted twice, reset.
