# Hive brain

Read this first. It is the shared memory for anyone working on Hive, human or agent: what we know, how sure we are, what is being tested, and exactly how to continue. When you learn something, update this file in the same commit as the evidence.

Last updated: Oct 27 2026, 16:20 IST.

## 1. The question

Can a swarm of AI coding agents that never message each other build real software by coordinating only through a shared git repository? And what limits how big and how correct such a swarm can get?

## 2. Current answer

On projects up to 1,340 tests and 12 agents: yes. Silent swarms finished every project they were given. They never gamed the tests, and collisions were rare and cheap.

Two things limit them today:

- **Cost is mostly onboarding.** Each worker spends about 110k tokens getting started, against about 3k to 5k per task after that.
- **Speed stops improving at around 6 to 12 workers.** The biggest task, and how late it gets claimed, sets the finish time.

The deeper limit is intent. On rules a model cannot guess, swarms passed every visible example but only 35 to 58% of the hidden tests when there was no one to ask (Gates 3 to 5, including rules written by an independent agent). 30 questions to a product owner added +28.6, +29.0 and +32.4 points on three different rule sets; 320 questions reached 98%. Gate 6 assigned questions per function at random and showed that questions **cause** the gain: 3 questions on a function added +44 points of edge-case accuracy, 1 question only +12, none +8. A rule needs several answered points to pin down, so questions are worth more in blocks of about 3 than spread one per function. Two strategies for choosing questions failed to beat free asking: coverage planning (Gate 4) and defaults-first (Gate 5). Where an owner's surprises sit depends on the owner.

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
| 7 Intent bandwidth | useful work per hour ≤ I/b | **Evidence that intent binds** (Gates 3, 4): hidden pass rises with questions (58 / 87 / 98% at 0 / 30 / 320). The rate law itself (I and b) is **not measured** |
| Coverage | edge error ≈ e_g·(1 − coverage of input classes by questions) | **Prediction failed** (Gate 4): coverage-planned 30 questions = free 30 questions |
| Questions per function | edge-accuracy gain +7.9 / +11.9 / +44.0 points at 0 / 1 / 3 questions on that function (3 − 0: +36.1, CI +20 to +51) | **Randomized** (Gate 6, one rule set, 6–7 functions per group). The earlier observational table (0 / +20 / +24 / +34, Gates 3–5) overstated the first question |
| Allocation of a fixed budget | concentrating about 3 questions per function beats one per function (model mean edge gain 25.9 vs 19.9 for 30 questions) | **Model** from the Gate 6 curve; gain(2) interpolated |
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
| Visible minus hidden gap | under 1 point when visible and hidden sample the same intent; 42 to 52 points when intent is missing (no questions) | Gates 1 to 4 |
| Guess accuracy without intent | 99 to 100% on happy paths, 66 to 73% on edge cases | Gates 3, 4 |
| Gain from 30 questions | +28.6, +29.0, +32.4, +25.0 points hidden (paired 95% CIs about ±12) | Gates 3 to 6 |
| Guessing baseline, edge calls | 73% (Gate 3), 66% (Gate 4), 54% and 60% (Gates 5, 6: independent rule-givers) | Gates 3 to 6 |
| Edge accuracy, function asked vs not | 96.1% vs 75.7% (observational: workers chose what to ask) | Gate 3 |
| Remaining error after 30 questions | 51 to 56% is NULL handling and caps on extremes | Gate 4 |
| Cost of questions | +12% tokens and about 2.5 min for 320 questions | Gate 3 |

## 5. Evidence log

| Gate | Date | What ran | Result |
| --- | --- | --- | --- |
| Real repos | Oct 27 | C compiler history (16 agents), FastRender (up to 2,000 agents) | Collisions rare and cheap; v1's κ ≈ 1/m was 10× off; no cliff in FastRender's build-fix rate |
| Simulation | Oct 27 | `sim/hive_sim.py`, experiments A to D, fitted then held out | Sampled checks with trace-back hold live bugs flat in N; v1's fixed-delay referee fails |
| Gate 0 | Oct 27 | Compiler history replayed against 620 hidden tests | Small steady live-bug count; bimodal lifetimes |
| Gate 1 | Oct 27 | 34 Claude workers, 6 swarms, SQL engine with SQLite as referee | No gaming; 2→6 builders bought 1.26×; onboarding dominates; foundation-first failed |
| Gate 2 | Oct 27 | 10× project, 2 / 6 / 12 long-lived workers | Onboarding law held; speed saturated near 6; collisions grew slower than predicted; first semantic conflict, repaired in 22 s |
| Gate 3, step 2 | Oct 27 | Protocol v2 (category claims, guarded landing), 8 and 12 workers | Onboarding law held a third time; guard blocked both would-be regressions; all 2,960 hidden tests pass; no gaming (gap ≤ 0.4 pts); finish time set by the tail |
| Gate 3, step 3 | Oct 27 | Intent test: 20 invented business rules, 3 swarms of 3, 0 / 30 / unlimited questions to a product owner | Hidden 58% / 87% / 98% (function-clustered 95% CIs 45–71, 78–94, 93–100); all predictions held; no cheating; the leftover errors are rules no question touched |
| Gate 4 | Oct 27 | Fresh rules; 0 questions, 30 free questions, 30 questions chosen by a coverage planner whose answers became tests | 47.8% / 76.8% / 76.4%: planning did not help (−0.4 pts, CI −12 to +11); kill condition fired; the +29-point gain from 30 questions replicated |
| Gate 7 | Oct 27 | A real company's 10 rules (Company X, name withheld), checked against its internal documents; no questions vs 15 questions answered from the documented policy | 32.8% → 49.6% hidden (+16.8, CI +6 to +31); the same team gained +21 from its answers; the biggest losses came from never being told the allowed input values; rules kept private |
| Gate 6 | Oct 27 | Second independent rule-giver; 0 questions, 30 free, and 0 / 1 / 3 questions per function assigned at random | Questions cause the gain (3 vs 0: +36 pts, CI +20 to +51); one question adds little (+12 vs +8); 'first question worth most' failed; concentration beats spreading (model); +25-point gain from 30 questions replicated a fourth time |
| Gate 5 | Oct 27 | Rules from an independent rule-giver agent; 0 questions, 30 free, 30 defaults-first | 34.6% / 67.0% / 62.2%: defaults-first did not help (−4.8 pts, CI −14.6 to +4.2) though delivered (37% of questions had NULL vs 10%); kill fired; +32.4-point gain from 30 questions replicated |

## 6. Prediction scorecard

All predictions are written down before the run, in each gate's `PREDICTIONS.md`.

- **Held:** intent is binding, and correctness rises with questions, all 5 intent predictions (Gate 3); no-questions baseline in range (Gate 4); gain from 30 questions in +15 to +43, treatment delivered, rules not guessable (Gate 5); questions cause the gain, fourth replication (Gate 6); onboarding law (Gates 2, 3); no gaming (Gates 1, 2, 3); guard keeps regressions off the tip of main (Gate 3; the blocked commit still sits in history next to its fix, so `--continue` should squash); no overlapping claims (Gate 3).
- **Failed:** the first question per function is worth the most (Gate 6: gain(1)/gain(3) = 0.27); defaults-first questions beat free questions (Gate 5: 62.2% vs 67.0%); coverage-planned questions beat free questions, and reach 95% (Gate 4: 76.4% vs 76.8%); free 30 questions in 78–92% (Gate 4: 76.8%); free askers leave 3+ functions unasked (Gate 4: 2); foundation-first is cheaper (Gate 1); speed of 3 to 4× at 12 workers (Gate 2: 2.3×); collisions growing as κ(N−1) (Gate 2: slower); finer claims lowering the time floor (Gate 3: 8.7 min against 7.8).
- **Untested:** a person answering live (Gate 7's answers came from documented policy); 24 workers; breakers at scale; gain at 2 questions and beyond 3; a concentrated allocation run head to head; which functions deserve the blocks.
- **Dropped before running:** 'one question per function before any gets a third'. Our own table predicted 0–1 points of effect against ±10 of noise, and Gate 6's curve later showed it would have been the worst allocation.
- **Flawed check, disclosed:** one cheating-signature rule (CHECKSUM +97) could be read off a visible example.

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
- **Intent interface** (Gates 3, 4):
  - Write every answer into a shared test at once.
  - Label each answer as a ruling on that input only. Builders stretched rulings into rules, within and across functions (Gate 4: about 45 of 139 failing calls).
  - Planning questions by coverage (Gate 4) and asking about defaults first (Gate 5) did not beat free asking. Don't rely on either.
  - Spend questions in blocks of about 3 per function, enough to triangulate a rule. One question per function buys little (Gate 6). Which functions get the blocks is still open.
  - Put the allowed input values (statuses, types, categories) in the spec. Their absence caused the largest losses with a real company's rules (Gate 7).
  - Read the company's own documents first. They overturned two of the owner's rules before any code was written (Gate 7).
  - Vary one thing per question. A question that mixed a small group with an invalid value taught the wrong rule (Gate 5, `nps_score`).

## 8. Open questions, most important first

1. **The intent curve.** How does hidden correctness grow with the number of answered values: 0, 10, 30, 100, 300 questions, repeated? This would turn limit 7 from evidence into a measured law.
2. **Which functions get the blocks.** With 3 questions per function, a 30-question budget covers only 10 of 20 functions. What predicts where the blocks pay most (spec vagueness, number of arguments, the builders' own confidence)? Also measure gain at 2 questions and at 5 or more.
3. **The tail.** Does largest-first claiming bring 12 workers under 7 minutes?
4. **The largest swarm this lab allows**: 20 workers with largest-first claiming.
5. **Turning intent into tests automatically**: the referee as the product.
6. **Breakers at scale**: do they shorten the 31-hour unseen-bug lifetime?

## 9. Next experiments, exactly

1. **Intent curve** (about 1.7M tokens per repeat). Fresh rules; teams of 3 with 0, 10, 30, 100 and 300 questions; then repeat. Fit hidden error against answered values, and register the form of the fit before the repeat.
2. **Largest-first at 12 and 20 workers** (about 4M tokens). Same project as Gate 3 step 2. Registered prediction to write first: 12 workers under 7.0 minutes.
3. **Self-registering modules** at 12 workers: conflicts per landing below 0.2.

## Related systems

- **T3 Code** (Ping.gg, open source; v0.1.0 on Oct 15 2026): a control surface for coding agents (Codex, Claude Code, Cursor and others) across desktop, web and phone. Parallel threads run in separate git worktrees. A person reviews diffs and approves, and `delegate_task` lets a parent agent start child agents.
  - **Contrast with Hive.** T3 Code helps one person *supervise* several agents, with the person as referee. Hive removes the supervisor: agents coordinate through claims and guarded landings, and tests are the referee.
  - **Model, not measured on T3 Code.** A person reviewing every landing is a serial gate (limit 2). Our 12-worker swarm landed about 4 changes a minute, so at 2 minutes per review it would need about 8 reviewers. Hive moves the person to intent (limit 7) instead.
  - **They complement each other.** T3 Code could serve as a Hive dashboard; Hive cannot work where there is no referee, and T3 Code can.

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
- Give 95% intervals clustered by function: the hidden tests come from about 20 functions, not 500 independent cases. One run per team is not a replication. Say when a comparison is observational.

## 12. Changelog

- **Oct 27 2026:**
  - Hive v1 doc analysed; real-repo measurements; simulator v2; Hive v2 doc (`docs/hive_v2.md`).
  - Gates 0, 1 and 2 run.
  - Protocol v2 built.
  - Gate 3 scale step run (8 and 12 workers).
  - Gate 3 intent step built, attempted twice (stopped), then run: 58% / 87% / 98% hidden at 0 / 30 / unlimited questions. Oracle unsealed.
- Accuracy audit: function-clustered confidence intervals added; "limit 7 measured" corrected to "evidence that intent binds"; the asked-vs-not comparison flagged as observational.
- Gate 4: coverage-planned questions vs free questions on fresh rules. No difference (76.4% vs 76.8%); kill condition fired; the +29-point gain from 30 questions replicated.
- Gate 5: an independent agent wrote the rules; defaults-first questions vs free. No help (62.2% vs 67.0%); kill condition fired; the gain from 30 questions replicated a third time (+32.4). Questions-per-function table pooled across Gates 3 to 5.
- T3 Code compared in Related systems.
- Gate 7: a real company's rules (Company X, name withheld), with its internal documents as the final authority. 15 answered questions lifted hidden correctness from 32.8% to 49.6%. Rules and answers are kept out of this public repo.
- Gate 6: the spread-the-budget test was dropped after a pre-flight calculation showed it could not detect its own predicted effect. Instead, 0/1/3 questions per function were randomly assigned. Questions cause the gain (+36 points for 3 vs 0); one question adds little; concentration beats spreading (model).
