# Hive brain

Read this first. It is the shared memory for anyone working on Hive, human or agent: what we know, how sure we are, what is being tested, and exactly how to continue. When you learn something, update this file in the same commit as the evidence.

Last updated: Oct 27 2026, after Gate 21.

## 1. The question

Can a swarm of AI coding agents that never message each other build real software by coordinating only through a shared git repository? And what limits how big and how correct such a swarm can get?

## 2. Current answer

On projects up to 1,340 tests and 12 agents: yes. Silent swarms finished every project they were given. They never gamed the tests, and collisions were rare and cheap.

Two things limit them today:

- **Cost is mostly onboarding.** Each worker spends about 110k tokens getting started, against about 3k to 5k per task after that.
- **Speed stops improving at around 6 to 12 workers.** On a 2-CPU machine the guard's full-suite runs per landing queue for the processor; on 24 cores the same 12-worker project finished in 3.5 minutes; limited to 4 CPUs on the same machine, 12.1 (Gates 10, 21). Caching main's test results in the guard saved 16% (Gate 21). Claiming the largest work first did not help (Gate 10).

The deeper limit is intent, and Gates 3 to 17 have now mapped it. On rules a model cannot guess, swarms pass every visible example but only 35 to 58% of hidden tests when nobody tells them the rules.

- **Builder questions help but hit a floor.** 30 questions add about +25 to +32 points (five rule sets). But builders only probe what they can imagine: about a fifth of errors survive any number of questions (Gate 12). The bottleneck is where questions point, not how many.
- **When the owner points, intent gets through.** One worked example per policy decision, chosen by the owner and given as tests (a *decision tour*), took builders to 89–96% hidden on three rule sets; with 17 questions on top, 95.2% and 98.2% (Gates 13–15, 17).
- **An owner with documents gets most of the way.** An extractor agent reads the handbook and picks inputs; the owner answers; handbook, answered examples and questions ship together: 93.8% on the same rules where the listing owner reached 98.2% (Gate 17). The gap sits entirely at decisions nobody wrote down (0.86 vs 1.00 of those errors fixed).
- **On a real company's rules (Gate 18):** 56 owner-confirmed examples took hidden correctness from 26.0% to 64.8%, and with 19 questions to 78.0% (Gate 7's best on the same rules: 49.6%). But the examples were agent-drafted QA cases the owner only confirmed, and they fixed no more than 19 builder questions (ratio 0.93). Conjecture: the examples' advantage needs the owner to *choose* the points.
- **Open:** a real owner choosing the examples, and real documents.

## 3. The law and how sure we are of each part

```
X_useful = min( N(1−f) / (1 + κ·d·(N−1)),   (1−f) / t_g,   I / b )
```

N agents; κ share of concurrent pairs that edit the same lines; d cost of one collision, in task lengths; f share of landings that carry a bug; t_g full-suite time of a central gate; I bits of intent entering per hour; b bits needed per unit of correct work.

Status tags: **established** means outside theory or our data on real agents; **model** means our formula, fitted on some cases and checked on held-out ones; **conjecture** means not yet tested.

| Limit | Rule | Status |
| --- | --- | --- |
| 1 Coupling | efficiency = 1/(1 + κd(N−1)) | Form established (USL contention); constants measured on one real project |
| 2 Gate | a serial gate caps landings at (1−f)/t_g | Established (queueing). Measured: t_g grows with CPU contention; finish ≈ 5.9 + 3.1·r minutes at 1 core per 6 workers, r = full-suite runs per landing (model, two points, Gate 21) |
| 3 Critical path | N ≤ W/D (Brent) | Established; seen binding in Gate 1 |
| 4 Threshold | bugs die out only if R < 1; with sampled checks and trace-back, live bugs = f(1−s)/s, independent of N | Branching threshold established; the N-independence is our model, matched in simulation within 3% |
| 5 Referee consumption | k adaptive landings on n hidden tests leak √(k/n); a Ladder gate leaks (log(kn)/n)^(1/3) | Established (Blum & Hardt 2015); not binding at our scale |
| 6 No universal referee | no automatic check decides arbitrary intent | Established (Rice) |
| 7 Intent bandwidth | useful work per hour ≤ I/b | **Evidence that intent binds** (Gates 3, 4): hidden pass rises with questions (58 / 87 / 98% at 0 / 30 / 320). The rate law itself (I and b) is **not measured** |
| Coverage | edge error ≈ e_g·(1 − coverage of input classes by questions) | **Prediction failed** (Gate 4): coverage-planned 30 questions = free 30 questions |
| Questions per function | share of a function's no-question edge errors fixed at 0 / 1 / 2 / 3 questions: 0.15 / 0.51 / – / 0.92 (Gate 6), 0 / 0.56 / 0.65 / 0.87 (Gate 8), 0.08 / 0.25 / 0.65 / 0.63 (Gate 11) | Gains are **randomized** (three rule sets). The one-parameter law E·(1 − (1−p)^q) (Gate 8 model) **failed** on Gate 11 (p 0.53, 0.56, then 0.35). Shape varies by rule set; conjecture: it saturates near the number of hidden decisions per function |
| Allocation of a fixed budget | 1–2 questions per function beat blocks of 3 on half the functions: 1.25× the errors fixed (CI 1.00 to 1.78); within the same functions the 3rd question added −0.01 and the 1st +0.17 | **Randomized, head to head**, one run, pairs matched on headroom (Gate 11) |
| Unreached floor | share fixed ≈ (1 − u/d)·(1 − (1−r)^q): d decisions per function, u of them outside what builders think to probe. Measured: 21% of no-question edge errors never fixed at 1, 2 or 4 questions per function; share 0.57 / 0.67 / 0.76 | Floor **measured** (Gate 12, one rule set); the formula is a **conjecture** written after the data |
| Decisions per function | one question fixes 0.69 of errors with 1–2 hidden decisions, 0.39 with 3–4 | **Randomized** (Gate 12, decisions set by the rule-giver); saturation point did not track decisions (ρ = 0.18) |
| Who chooses the points | 50 owner-chosen values (decision tour) fix 0.76 and 0.98 of edge errors (Gates 13, 14); ~51 builder-chosen values fix 0.28; tour + 17 questions 0.89. Tour reaches 91% of errors questions leave | **Randomized**, replicated on two rule sets (Gates 13, 14), one run per team; no hidden input copied |
| Contrast examples | adding one contrast per decision to the tour: −4.8 points (CI −11.4 to +0.6), more calls broken (19 vs 13) | **Randomized**, one run (Gate 14); contrasts dropped |
| Tour from documents | handbook (20 clear, 15 vague, 15 omitted decisions) given to builders: 0.65 of edge errors fixed; extractor-picked inputs answered by the owner: 0.74; owner's own tour: 0.94. Functions with nothing omitted: 1.00 for both handbook paths | **Randomized**, one run (Gate 15); X − H +3.4 (CI −5 to +15), T − X +12.0 (CI −0.4 to +23.6) |
| Stacked documented-owner interface | extracted tour +19.4, then handbook +10.2, then 17 questions +12.2 points: 83.2% hidden; 0.79 of edge errors fixed where a decision was omitted | **Randomized**, one run (Gate 16); extracted tour's gain varied +36 (Gate 15) to +19 (Gate 16) |
| Two owners, same rules | listing owner (tour + 17 questions) 98.2% vs documented owner (handbook + extracted tour + 17 questions) 93.8%: +4.4 (CI −2.4 to +11.4); gap entirely at omitted decisions (1.00 vs 0.86) | **Randomized**, one run, fair copy rule (Gate 17) |
| Real company's rules | owner-confirmed (agent-drafted) examples +38.8 points; 19 questions +30.4; both +52.0 (78.0%); examples / questions edge errors fixed 0.93; examples broke 26 calls, questions 60 | **Randomized**, one run, 10 real functions (Gate 18); aggregates only |
| Onboarding | tokens ≈ c_on·N + c_task·T | **Model**, held out three times (Gates 1, 2, 3) |
| Tail | finish ≥ max(work/N, longest task + when it starts) | Established (scheduling theory); seen binding in Gate 3, not in Gate 10 (big families were claimed in the first half-minute under either rule) |
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
| Gain from 30 questions | +28.6, +29.0, +32.4, +25.0, +29.4 points hidden (paired 95% CIs about ±13) | Gates 3 to 6, 8 |
| Guessing baseline, edge calls | 73% (Gate 3), 66% (Gate 4), 54%, 60% and 57% (Gates 5, 6, 8: independent rule-givers) | Gates 3 to 6, 8 |
| p, if the geometric law is forced | 0.53, 0.56, 0.35: not a constant | Gates 6, 8, 11 |
| Spillover to unasked functions | 0.15, 0, 0.08 of their errors; up to 18 of 27 on one function next to a well-asked neighbour | Gates 6, 8, 11 |
| Cost of an intent gate | $6.0 for 2 teams (Gate 8), $8.1 for 3 teams (Gate 11), $10.3 and $9.8 for 4 teams (Gates 12, 13), $7.2 for 3 teams (Gate 14), $10.5, $10.2 and $10.2 for 4 teams plus an extractor (Gates 15–17), at list price; about $0.7–1.2 per builder; reported tokens include cache reads | Gates 8, 11 |
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
| Gate 21 | Oct 27 | Cached guard vs Gate 3's guard, 12 workers each, container limited to 4 CPUs | F12 12.1 min (3.5 unlimited), C12 10.2 (0.84×); 61% cache hits; no extra breakage; G1, G3–G5 held, G2 failed |
| Gate 10 | Oct 27 | Largest-first claiming vs Gate 3's claiming, 12 workers each, same 24-core machine | F12 3.5 min, L12 4.3 min (tail 0.1 vs 0.7); kill fired; both 2.5× faster than Gate 3 on 2 CPUs; hidden suite regenerated on SQLite 3.49.1 (2,220 tests) |
| Gate 18 | Oct 27 | Real company's rules (private); N0 vs owner-confirmed examples vs 19 questions vs both | 26.0 / 64.8 / 56.4 / 78.0%; R1, R3, R5 held; R2 failed (examples fixed 0.93× what questions did); aggregates only |
| Gate 17 | Oct 27 | Same rules, fair copy rule: N0 vs extracted tour vs documented owner (HXQ) vs listing owner (TQ) | 46.4 / 87.8 / 93.8 / 98.2%; F1, F3–F6 held; F2 failed (gap +4.4, between decision thresholds); gap entirely at omitted decisions |
| Gate 16 | Oct 27 | Handbook + extracted tour + questions, stacked | 41.4 / 60.8 / 71.0 / 83.2%; each layer added; S1 (90%), S4, S5 failed; copy rule found to penalize the extractor (17 of 50 picks dropped); a document's silence misled builders |
| Gate 15 | Oct 27 | Rule-giver also writes a handbook (20 clear, 15 vague, 15 omitted); N0 vs owner's tour vs handbook vs extractor-built tour | 44.6 / 92.6 / 77.2 / 80.6%; extracted tour keeps 0.75 of the tour gain; omitted decisions are the floor; X1–X4, X6 held, X5 failed (14 extractor picks were exact hidden inputs, dropped) |
| Gate 14 | Oct 27 | New rule-giver; N0 vs tour vs tour plus a contrast per decision | Tour replicated: 42.4% → 95.6% (+53.2); contrasts 90.8% and more breakage; C2, C3 failed; contrasts dropped |
| Gate 13 | Oct 27 | Owner's decision tour (one example per declared decision, as visible tests) vs 17 builder questions vs both | Hidden 57.8 / 67.2 (Q) / 89.4 (tour) / 95.2% (both); all five predictions held; tour over-generalizes a little (27 calls broken), questions repair it (15) |
| Gate 12 | Oct 27 | Rule-giver sets 1–4 hidden decisions per function (5 each, declared privately); teams ask 0 / 1 / 2 / 4 questions on every function | Hidden 36.8 / 68.2 / 75.0 / 81.6%; D1 held (few decisions: first question +0.30 more), D2 and D4 failed; 21% of errors unreached by any team, each a decision no question probed |
| Gate 11 | Oct 27 | Fourth independent rule-giver; N0 first, then functions paired by N0 errors; S (2 / 1 questions per pair) vs B (3 / 0), 30 each | S fixed 1.25× B's errors (CI 1.00 to 1.78); hidden 36.6 / 58.6 / 55.6%; the 3rd question added nothing within the same functions; Gate 8's p-law failed (p = 0.35); P2, P3, P4 failed |
| Gate 8 | Oct 27 | Third independent rule-giver; 0 questions vs 0 / 1 / 2 / 3 questions per function at random (5 each), run in Docker with `lab/run_gate.py` | 42.4% → 71.8% hidden (+29.4, CI +16 to +43); gains 0 / +21.0 / +26.1 / +39.1; R3 failed and its kill fired; Gate 6's weak first question traced to a headroom imbalance; p ≈ 0.55 fits both gates |
| Gate 5 | Oct 27 | Rules from an independent rule-giver agent; 0 questions, 30 free, 30 defaults-first | 34.6% / 67.0% / 62.2%: defaults-first did not help (−4.8 pts, CI −14.6 to +4.2) though delivered (37% of questions had NULL vs 10%); kill fired; +32.4-point gain from 30 questions replicated |

## 6. Prediction scorecard

All predictions are written down before the run, in each gate's `PREDICTIONS.md`.

- **Held:** intent is binding, and correctness rises with questions, all 5 intent predictions (Gate 3); no-questions baseline in range (Gate 4); gain from 30 questions in +15 to +43, treatment delivered, rules not guessable (Gate 5); questions cause the gain, fourth replication (Gate 6); questions cause the gain again, fifth replication, curve rises, rules not guessable, treatment delivered (Gate 8, R1, R2, R4, R5); spread beats blocks of 3 head to head, treatment delivered, rules not guessable (Gate 11, P1, P5, P6); fewer hidden decisions, more from the first question, curve rises (Gate 12, D1, D3, D5, D6); owner-chosen points beat builder-chosen points 2.7×, tour plus questions ≥ 0.80, tour reaches what questions miss (Gate 13, all of M1–M5); the tour replicates on a new rule set (Gate 14, C1); a handbook-derived tour keeps half the gain or more, beats handing over the handbook, and omitted decisions are its floor (Gate 15, X1–X4, X6); handbook and questions each add on top of an extracted tour (Gate 16, S2, S3); fairly scored extracted tour ≥ +30, documented stack ≥ 85%, listing stack ≥ 92% (Gate 17, F1, F3–F5); examples carry a real company's intent, and with questions reach 75% (Gate 18, R1, R3, R5); onboarding law (Gates 2, 3); no gaming (Gates 1, 2, 3); guard keeps regressions off the tip of main (Gate 3; the blocked commit still sits in history next to its fix, so `--continue` should squash); no overlapping claims (Gate 3).
- **Failed:** the cached guard finishes in ≤ 0.75× (Gate 21: 0.84×); largest-first claiming cuts the finish and the tail at 12 workers (Gate 10: 4.3 vs 3.5 min); owner-confirmed (agent-drafted) examples beat builder questions 1.3× on real rules (Gate 18: 0.93); the listing owner beats the documented owner by ≥ 5 points (Gate 17: +4.4, CI −2.4 to +11.4); the full documented stack reaches 90%, closes the omitted-decision floor, and the extracted tour replicates at ≥ +25 (Gate 16: 83.2%, 0.79, +19.4); the extracted tour keeps ≥ 40 of 50 inputs after the copy filter (Gate 15: 36; 14 were exact hidden inputs); contrasts halve tour breakage, and do not cost correctness (Gate 14: 19 vs 13 broken; −4.8 points); saturation point tracks decisions (Gate 12: ρ = 0.18); 4 questions per function reach 0.80 of errors (Gate 12: 0.76); Gate 8's one-parameter law on a new rule set (Gate 11: p = 0.35, outside 0.40–0.70); 3-question functions fix ≥ 0.75 (Gate 11: 0.63); the first question fixes ≥ 0.35 (Gate 11: 0.25); the first question is worth less than half of three (Gate 8: 0.54; its kill fired and "blocks of 3" was withdrawn); a surprise-count law found post hoc in Gate 8 (worse than question count on held-out Gate 6); the first question per function is worth the most (Gate 6: gain(1)/gain(3) = 0.27, later traced to a headroom imbalance); defaults-first questions beat free questions (Gate 5: 62.2% vs 67.0%); coverage-planned questions beat free questions, and reach 95% (Gate 4: 76.4% vs 76.8%); free 30 questions in 78–92% (Gate 4: 76.8%); free askers leave 3+ functions unasked (Gate 4: 2); foundation-first is cheaper (Gate 1); speed of 3 to 4× at 12 workers (Gate 2: 2.3×); collisions growing as κ(N−1) (Gate 2: slower); finer claims lowering the time floor (Gate 3: 8.7 min against 7.8).
- **Untested:** a human owner's tour or handbook; handbook plus extracted tour plus questions stacked; a person answering live (Gate 7's answers came from documented policy); 24 workers; breakers at scale; gain beyond 3 questions; whether questions-to-saturation tracks the number of hidden decisions per function; a repeat of Gate 11.
- **Dropped before running:** 'one question per function before any gets a third'. Our own table predicted 0–1 points of effect against ±10 of noise, and Gate 6's curve later showed it would have been the worst allocation. (Later corrected: Gate 8 traced that curve to a headroom imbalance, and Gate 11 found spreading beats blocks of 3, 1.25×.)
- **Flawed check, disclosed:** one cheating-signature rule (CHECKSUM +97) could be read off a visible example.

## 7. Design as of now (Hive v2 plus protocol v2)

- Workers never talk. Long-lived workers take task after task, because onboarding costs about 20 tasks' worth of tokens.
- Claims name test categories (`gate3/tools/claim.py`); overlapping claims are refused and races resolved by commit order.
- Landing is guarded (`gate3/tools/land.py`): no new duplicate definitions, and no test that passes on main may fail after the change.
- Two suites: visible tests guide the workers, hidden tests judge. Hidden suites are never committed.
- No founder phase: the swarm shapes its own extension points within minutes.
- **Next changes:**
  - Guard caches main's suite results per commit (Gate 21: same safety, 16% faster on a CPU-bound machine). Give swarms about a core per worker.
  - Modules register themselves, which removes most conflicts.
  - `land.py --continue` squashes the fix into the blocked commit, so every commit on main passes.
- **Intent interface** (Gates 3, 4):
  - Write every answer into a shared test at once.
  - Label each answer as a ruling on that input only. Builders stretched rulings into rules, within and across functions (Gate 4: about 45 of 139 failing calls).
  - Planning questions by coverage (Gate 4) and asking about defaults first (Gate 5) did not beat free asking. Don't rely on either.
  - Spread a fixed budget across functions, about 2 per function before any gets a third. Blocks of 3 lost head to head (Gate 11: 1.25×), and within the same functions the 3rd question added nothing. The value of the 1st and 3rd questions varies with the rule set.
  - **Step one: the owner gives a decision tour**, one worked example per policy decision, as tests (Gates 13, 14: 57.8% → 89.4% and 42.4% → 95.6% hidden; 67.2% for the same number of builder-chosen answers). Do not add contrast examples (Gate 14: they moved boundaries). **Step two: builders ask questions around it** (95.2% with both). Builder questions alone hit a floor at decisions builders cannot imagine (Gate 12).
  - **When the owner has documents rather than a list:** ship the handbook, examples an extractor picked and the owner answered, and builder questions together; each layer added (Gate 16: 60.8% → 71.0% → 83.2%). Prefer the owner's own decision list when it can be had (about 10 points better). Treat a document's silence as unknown, not as "standard": a handbook that waved at "the standard" misled builders on an unwritten rule (Gate 16).
  - A question that confirms the builders' guess buys nothing; confirmation does not mean the function is right (Gate 8, conjecture).
  - Put the allowed input values (statuses, types, categories) in the spec. Their absence caused the largest losses with a real company's rules (Gate 7).
  - Read the company's own documents first. They overturned two of the owner's rules before any code was written (Gate 7).
  - Vary one thing per question. A question that mixed a small group with an invalid value taught the wrong rule (Gate 5, `nps_score`).

## 8. Open questions, most important first

1. **The intent curve.** How does hidden correctness grow with the number of answered values: 0, 10, 30, 100, 300 questions, repeated? This would turn limit 7 from evidence into a measured law.
2. **Real owners.** Every owner so far was an agent that wrote its own rules. Does the documented-owner interface hold with a real company's documents and a person answering? Does a cheap elicitation step ("here are the decisions we found; which are missing?") recover the unwritten ones (Gate 17's remaining gap)?
3. **The guard's floor.** CPU per guard check sets the finish on small machines (Gate 21: 3.5 → 12.1 minutes from 24 to 4 CPUs). Caching saved 16%; the model puts the floor near 5.9 minutes on that load. Does a near-100% cache plus checking only touched categories reach it without letting regressions through?
4. **The largest swarm this lab allows**: 20 workers with largest-first claiming.
5. **Turning intent into tests automatically**: the referee as the product.
6. **Breakers at scale**: do they shorten the 31-hour unseen-bug lifetime?

## 9. Next experiments, exactly

1. **Owner-chosen examples on real rules** (needs the owner's time): the founder writes one example per decision for Gate 7's functions, without seeing the QA list; compare with the same number of builder questions. Tests the Gate 18 conjecture.
2. **The documented-owner interface on real documents** (needs the company's policy pages).
2. **Repeat Gate 11 on a new rule-giver** (about $8.4).
3. **Intent curve** (about 1.7M tokens per repeat). Fresh rules; teams of 3 with 0, 10, 30, 100 and 300 questions; then repeat. Fit hidden error against answered values, and register the form of the fit before the repeat.
4. **Guard at its floor** (about $30): store main's results before pushing (hit rate near 100%) and check touched categories plus a sample, on 4 CPUs. Prediction from the Gate 21 model: about 9 minutes or less, with no more breaking commits than the full guard.
5. **Self-registering modules** at 12 workers: conflicts per landing below 0.2.

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

Open a Claude Code session on this repo (laptop, VM or phone) and say "Continue Hive: run the next ready experiment in lab/QUEUE.md".
- `lab/QUEUE.md` holds the handoff note and the ready experiments.
- `lab/README.md` explains the scripts.
- One command runs a whole intent gate: `python3 lab/run_gate.py lab/experiments/<config>.json`.

Rules of the lab:

- Register predictions before launching.
- Change one thing per experiment.
- Every worker logs CLAIM, LAND, CONFLICT and BLOCKED events to `HIVE_LOG`.
- Hidden suites and private intent stay out of the repo until their test has run, and real companies never appear.
- Report failures as plainly as successes.
- Give 95% intervals clustered by function, say when a comparison is observational, and remember that one run per team is not a replication.

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
- Lab: `lab/` runs a whole gate in one command with real headless Claude Code workers, so any session (including from a phone) can continue from `lab/QUEUE.md`. Gate 8 predictions registered.
- Gate 7: a real company's rules (Company X, name withheld), with its internal documents as the final authority. 15 answered questions lifted hidden correctness from 32.8% to 49.6%. Rules and answers are kept out of this public repo.
- Gate 22 (store-before-push guard) aborted: all workers hit the account's usage limit; to be rerun from scratch.
- Gate 21: under a controlled 4-CPU limit, Gate 3's setup took 12.1 minutes (3.5 unlimited): CPU per guard check sets the finish. A cached guard (main's results stored per commit; 61% hits) finished in 10.2 (0.84×), with no extra breakage. Two-term model of the finish fitted.
- Gate 10: largest-first claiming did not beat Gate 3's claiming (4.3 vs 3.5 minutes; kill fired). Both swarms finished 2.5× faster than Gate 3 on 24 cores: the guard's CPU cost on small machines, not claim order, set Gate 3's finish. gen2.py made Python 3.11-compatible (identical output); referee SQLite version mismatch found and disclosed.
- Gate 18: a real company's rules (Gate 7, private; aggregates only). Owner-confirmed examples 64.8%, 19 questions 56.4%, both 78.0% (N0 26.0%). Examples did not beat questions (0.93×) when they were agent-drafted; conjecture: the owner must choose the points.
- Gate 17: documented owner (handbook + extracted tour + questions) 93.8% vs listing owner (tour + questions) 98.2% on the same rules, with a fair copy rule (extractor picks equal to hidden inputs kept, those calls unscored). Gap +4.4, between the decision thresholds, entirely at omitted decisions. Current answer rewritten as the measured intent interface.
- Gate 16: the stacked documented-owner interface: extracted tour 60.8%, + handbook 71.0%, + 17 questions 83.2% (N0 41.4%). Each layer added; the 90% target and floor closure failed. Found a lab flaw: the copy rule drops the extractor's best picks. Found that a document's silence can mislead ("follow the standard").
- Gate 15: tour from a handbook. An extractor agent read only the handbook (20 clear, 15 vague, 15 omitted decisions) and picked inputs; the owner answered them. 80.6% hidden, against 77.2% for the handbook itself, 92.6% for the owner's own tour and 44.6% for nothing. The practical first step of the intent interface is documents → extractor → owner answers → tests.
- Gate 14: the tour replicated on a new rule-giver (42.4% → 95.6%). One contrast example per decision lowered it to 90.8% and broke more calls: contrasts move boundaries rather than pin them. Dropped.
- Gate 13: the owner's decision tour (50 examples as visible tests) against 17 builder questions and both. Tour 89.4%, questions 67.2%, both 95.2% hidden (N0 57.8%); every prediction held; 0/158 hidden inputs near-copied; no hardcoding. The tour becomes step one of the intent interface. Failure mode: over-generalization of a leniency, repaired by questions.
- Gate 12: the rule-giver set 1–4 hidden decisions per function; teams asked 0/1/2/4 questions on every function. Few decisions make the first question stronger (D1 held), but the saturation point did not track decisions (D2 failed), because a floor of 21% of errors was never reached by any team: decisions builders never thought to probe. Bottleneck reframed as where questions point.
- Gate 11: spread (2/1 per matched pair) vs blocks (3/0), with N0 run first so pairs are matched on headroom (`run_gate.py` stratified mode). Spread won (1.25×, CI 1.00–1.78), but Gate 8's p-law failed (p = 0.35; the 3rd question was worth nothing within the same functions). Law withdrawn; spreading kept as the default. First attempt stopped at a usage limit before any rules existed and was rerun from scratch.
- Gate 8: 0/1/2/3 questions per function at random, on a third rule-giver, run in Docker on a laptop. Questions cause the gain again (+39 at 3 vs 0); R3 failed and its kill fired. Gate 6's weak first question was a headroom imbalance; one law (each answer fixes about half the remaining errors, p ≈ 0.55) fits both gates; "blocks of 3" withdrawn in favour of one question per function first. A post-hoc surprise law failed its held-out test. Pre-flight power note added before scoring.
- Gate 6: the spread-the-budget test was dropped after a pre-flight calculation showed it could not detect its own predicted effect. Instead, 0/1/3 questions per function were randomly assigned. Questions cause the gain (+36 points for 3 vs 0); one question adds little; concentration beats spreading (model).
