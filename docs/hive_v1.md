# Hive: a swarm that scales by not talking

Oct 27, 2026

## Summary

Hive is a sandbox where thousands of coding agents build one codebase
without ever messaging each other. They coordinate only through a shared
world of code, signals and memory.

The bet: coordination cost, not model quality, is what caps today\'s
agent teams. Remove the conversations and cut the coupling between
pieces of work, and useful output should keep rising from 10 to 1,000
agents instead of peaking at 3--4.

The core idea is not new: LLM agents that coordinate through a shared
environment already exist in papers and small open-source tools. Nobody
has shown it holds at thousands of agents on real software. That proof,
and the coupling law behind it, is what Hive adds.

## The law

Hypothesis, now supported in simulation (see Simulation evidence): three
ceilings limit how large an agent swarm can usefully grow, and they
combine like resistors in parallel.

\\frac{1}{N\_{max}} = \\frac{1}{N\_{coupling}} + \\frac{1}{N\_{span}} +
\\frac{1}{N\_{referee}}

-   **Coupling.** κ is the chance two concurrent changes collide; with m
    independent regions, κ ≈ 1/m, and N_coupling ≈ 2.7m. Past it, a
    silent swarm does not slow down. It saturates: extra agents mostly
    waste work, and the cost of each finished task climbs.

-   **Span.** W is total work and D the critical path, the longest chain
    of steps that must happen in order. N_span ≈ 1.5W/D, because no
    swarm beats the critical path (Brent\'s theorem).

-   **Referee.** q is the share of bad changes the gate catches and τ
    the time to find an escaped bug. Bugs spread like an epidemic once R
    = (1 − q)·N·τ/m passes about 1.65, and efficiency falls off a cliff.
    A gate that traces each caught bug to its source removes the cliff.

Agents that talk to each other add a further cost that grows with every
pair (Brooks\'s law). The simulation did not model talking; the studies
below did.

Two consequences follow. Halving coupling roughly doubles the useful
swarm, so shapers must keep cutting the work finer as agents are added.
And detection time bites harder than the simple formula suggests, so the
gate must be fast as well as accurate.

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Study                                                                                                                  Setup               What it shows
  ---------------------------------------------------------------------------------------------------------------------- ------------------- -------------------------------------
  [Google                                                                                                                180 setups, 3 model Multi-agent gained 80.9% on parallel
  Research](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/),   families            work and lost 39--70% on sequential
  Jan 2026                                                                                                                                   work. Agents that neither talk nor
                                                                                                                                             check amplified errors 17.2×.

  [Anthropic C compiler](https://www.anthropic.com/research/building-c-compiler), Feb 2026                               16 agents, \~2,000  Parallelism was easy across many
                                                                                                                         sessions, \~\$20K,  failing tests. On one giant task (the
                                                                                                                         no orchestrator     Linux kernel), all 16 hit the same
                                                                                                                                             bug until a GCC oracle split the
                                                                                                                                             work.

  [Cursor](https://cursor.com/blog/scaling-agents), Jan 2026                                                             Hundreds of agents, With shared locks, 20 agents slowed
                                                                                                                         \~1 week, 1M+ lines to the throughput of 2--3. Planners
                                                                                                                                             plus workers let hundreds push to one
                                                                                                                                             branch with minimal conflicts.

  [Pressure-field coordination](https://arxiv.org/abs/2601.08129), Jan 2026                                              1,350 trials, 1--4  Coordinating only through a shared
                                                                                                                         agents, scheduling  artifact solved 48.5%, versus 11.1%
                                                                                                                                             for conversation and 1.5% for
                                                                                                                                             hierarchy.

  [CodeCRDT](https://arxiv.org/abs/2510.18893), Oct 2025                                                                 600 trials, up to 5 Low-coupling tasks sped up; highly
                                                                                                                         agents, code        coupled ones slowed. About 5--10% of
                                                                                                                                             runs had semantic conflicts.

  [MAST, UC Berkeley](https://arxiv.org/abs/2503.13657), 2025                                                            7 multi-agent       Many failures come from
                                                                                                                         frameworks, 200+    organizational design and
                                                                                                                         tasks               coordination, not from the individual
                                                                                                                                             agents.
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

The compiler run is the law in miniature: one giant coupled task made 16
agents worth one, and decoupling it with an oracle restored parallelism.
Google\'s 17.2× is the caveat: silence only works when a strong verifier
stands between agents and the shared code.

## Does this exist yet

Partly. Silent agents that coordinate through a shared environment
exist, including for code. Nobody has shown them working at 1,000 agents
on real software, and nobody treats decoupling as an active, continuous
job.

  -----------------------------------------------------------------------------------------------------------------------------------------------
  System                                                                                What it does             Scale shown   What\'s missing
  ------------------------------------------------------------------------------------- ------------------------ ------------- ------------------
  Stigmergy, blackboards, tuple spaces (1959--1985)                                     Coordination through a   Decades of    Not built for LLM
                                                                                        shared environment       use in        agents or code
                                                                                        instead of messages      robotics and  
                                                                                                                 classic AI    

  [Pressure-field coordination](https://arxiv.org/abs/2601.08129), Jan 2026             LLM agents improve a     1--4 agents,  Not code; coupling
                                                                                        shared artifact guided   meeting       assumed fixed; the
                                                                                        by quality \"pressure\"  scheduling    author lists
                                                                                        that decays over time                  coupling penalties
                                                                                                                               as future work

  [CodeCRDT](https://arxiv.org/abs/2510.18893), Oct 2025                                Agents write into one    Up to 5       Projects its own
                                                                                        shared code document and agents        breakeven at about
                                                                                        claim TODOs by observing               20 agents
                                                                                        it                                     

  [Codebolt                                                                             Coding agents never      Vendor        Vendor figures
  StigmergySwarm](https://docs.codebolt.ai/docs/concepts/multi-agent/stigmergy-swarm)   message; decaying        reports       only; no
                                                                                        pheromones, locks,       near-linear   independent study
                                                                                        bidding, reputation      scaling to    
                                                                                        voting                   200 agents    

  [Cursor long-running agents](https://cursor.com/blog/scaling-agents), Jan 2026        Planners, workers and a  Hundreds of   Hierarchical, not
                                                                                        judge on one repo        agents for    silent; no
                                                                                                                 weeks         published scaling
                                                                                                                               curve

  [Anthropic agent teams](https://www.anthropic.com/research/building-c-compiler), Feb  16 agents coordinate     16 agents     Decoupling was
  2026                                                                                  through git and lock                   done by a human
                                                                                        files, no orchestrator                 (the GCC oracle)
  -----------------------------------------------------------------------------------------------------------------------------------------------

Small open-source tools apply the same idea to coding fleets, such as
[dot_swarm](https://pypi.org/project/dot-swarm/) and
[Anthills](https://pypi.org/project/anthills/).

What Hive adds:

1.  **Shapers**: agents whose only job is to lower coupling as the swarm
    grows. They automate what the GCC oracle did by hand.

2.  **A scaling law with a coupling term**, tested by measuring the peak
    swarm size against measured coupling.

3.  **A 1,000-agent wind tunnel** on real software with an external test
    suite, run independently and published.

4.  **One world**: code, signals and a decaying shared memory in a
    single sandbox.

## Architecture

Hive has one rule: workers never talk to each other, so every
interaction runs through the shared world.

![Hive architecture · worker swarm, shared world, cockpit and
shapers](media/image1.png){width="6.0in" height="4.223214129483814in"}

Hive architecture · worker swarm, shared world, cockpit and shapers

Workers sense the field and brain, act in their own forks, and leave
traces; only the merge gate writes to main. You and the shapers change
the world itself, never the workers.

## Core mechanics

Every worker runs the same five-step loop, and no step involves another
agent.

1.  **Sense.** An idle worker picks the strongest unclaimed pressure in
    the field, such as a cluster of failing tests in one module. It
    loads a context pack: that code slice, the brain\'s notes for that
    region, and nearby signals.

2.  **Claim.** It takes a lease on the region that expires in minutes
    unless progress renews it. A crashed or stuck worker simply lets its
    lease lapse; nothing waits on it.

3.  **Act.** It works in its own forked sandbox and runs the local
    tests.

4.  **Land.** The merge gate rebases the change and runs the full suite.
    Passing changes reach main. Failures add pressure where they broke,
    and the work returns to the field.

5.  **Leave a trace.** The worker writes what it decided and learned to
    the brain, tagged with where it came from, then exits. The next
    worker starts fresh.

Around that loop, five system mechanisms keep the swarm healthy:

-   **Evaporation.** Every signal and memory has a half-life and fades
    unless reused. In the pressure-field study, decay lifted the solve
    rate from 86.7% to 96.7% on easy problems, though not significantly
    at 30 trials.

-   **Escalation.** Where pressure stalls, the region is re-offered to a
    stronger model, so cheap models do routine work. This also counters
    what Cursor saw in flat swarms: agents avoiding hard tasks.

-   **Shaping.** Shapers watch for hot spots where landed changes keep
    breaking each other. They respond by changing the world, never by
    assigning work: splitting a module, fixing an interface, writing
    contract tests, or building an oracle. Their scorecard is measured
    coupling going down.

-   **Steering.** A human edits the goal, a belief in the brain, or a
    pressure weight. That edit becomes pressure everywhere it applies,
    so a thousand workers change course without one message.

-   **Unlimited context, honestly.** Total context (code, brain,
    history) grows without limit. Each worker\'s working set stays small
    and local, which is what keeps the swarm fast.

## The wind tunnel

One experiment can prove or kill the law: the same project, three
coordination styles, swarm sizes from 10 to 1,000 agents. Run it before
building anything bigger.

-   **Project:** a clean-room reimplementation judged by an existing
    external test suite, such as a JavaScript engine against test262 or
    a SQL engine against SQLite\'s sqllogictest. The suite is the
    referee, and agents cannot rewrite a suite they did not write.

-   **Sizes:** 10, 30, 100, 300 and 1,000 agents, with the same models
    and per-agent budget in every arm.

-   **Measures:** tests passing per hour and per dollar; coupling κ,
    measured as the share of landed changes that break another agent\'s
    in-flight work; rework rate; time spent waiting at the merge gate.

  ------------------------------------------------------------------------
  Arm        Coordination               Prediction if the law holds
  ---------- -------------------------- ----------------------------------
  A: Talking Orchestrator plus messages Peaks early, then declines
             between agents             

  B: Silent  Shared world only, no      Keeps rising until coupling bites,
             shapers                    then bends

  C: Hive    Shared world plus shapers  Keeps rising past 300 agents as
                                        measured κ falls
  ------------------------------------------------------------------------

**Proves it:** arm C keeps climbing past 300 agents while A has peaked,
and across runs the peak size tracks 1/κ. **Kills it:** arm C peaks
below 100 agents like A. Either result is worth publishing.

## Simulation evidence

A simulation with no formulas coded in reproduced all three ceilings,
and the combined law predicted 70 unseen swarms within 2× (R² 0.955). It
also corrected two parts of the law above and produced one design rule:
the gate must trace bugs to their source.

Nothing in the simulation is scripted beyond the mechanics. Agents claim
a task, work for a random time, and land the change through a gate. Each
task writes one of m regions, and a landing forces anyone else in that
region to restart. Tasks sit in a dependency graph D layers deep. A
change can carry a fresh bug or inherit one from the region it writes or
reads. The gate catches a fraction q; an escaped bug is found after a
delay τ (in average task lengths) and reverted along with everything
infected in its region. 2,265 runs in total.

![Hive simulator, Oct 2026 · 240 configurations run with and without
trace-back](media/image2.png){width="6.0in"
height="2.964284776902887in"}

Hive simulator, Oct 2026 · 240 configurations run with and without
trace-back

  ------------------------------------------------------------------------
  Test         Result                               What it changes
  ------------ ------------------------------------ ----------------------
  Coupling     Efficiency depended only on agents   Coupling ceiling ≈
  only, 105    per region, and halved at 2.9 agents 2.9m
  runs         per region for 16, 64 and 256        
               regions alike                        

  Coupling     1,024 agents on 16 regions still     Silent swarms saturate
  past the     produced 69× one agent\'s output, at and get expensive; the
  knee         7% efficiency                        peak-and-decline in
                                                    The law was wrong

  Referee      R explained 94% of efficiency; half  The cliff is real, and
  only, 480    efficiency at R ≈ 1.65; fitted       slow detection is
  runs         exponents (1−q) 1.01, m 1.02, N      worse than the formula
               1.27, τ 1.45                         says

  Trace-back   Efficiency 11% → 77%; rework per     The merge gate must
  gate, 82     task 6.2 → 0.08                      bisect failures to
  swarms past                                       their source
  the cliff                                         

  Combined,    70 of 70 held-out predictions within Ceilings combine like
  1,680 runs   2×, R² 0.955; adding the ceilings    resistors in parallel
               beat taking the smallest (99% vs 90% 
               within 2×)                           
  ------------------------------------------------------------------------

The updated law:

\\frac{1}{N\_{max}} = \\frac{1}{N\_{coupling}} + \\frac{1}{N\_{span}} +
\\frac{1}{N\_{referee}}

Here N_coupling ≈ 2.7m, N_span ≈ 1.5W/D, and N_referee ≈ 6.8 · (m / ((1
− q) · τ\^1.45))\^0.79, with the exponents on m and (1 − q) rounded from
1.02 and 1.01. Coupling was the binding ceiling in 81 of 140
configurations, which makes shapers the most valuable part of Hive.

This tests self-consistency, not reality: the simulated agents are not
language models. The coupling result is close to guaranteed by the
model\'s symmetry, and the law overestimates swarms above about 250
agents by up to 1.8×. The referee cliff, the trace-back effect and the
resistor rule are what a real 10--50 agent run should test first. Code:
sim.py, experiments.py and analyze_e3.py, shared in the chat.

## Risks and open questions

The biggest risks are cost, a referee that can be gamed, and coupling
that refuses to go down.

-   **Cost.** Anthropic\'s 16 agents cost about \$20,000 over two weeks.
    At that rate, 1,000 agents would cost roughly \$1.25M per two weeks,
    so cheap worker models and escalation are mandatory.

-   **Gaming the referee.** Agents optimize whatever is measured.
    External suites, several independent checks, and spot review by
    humans are the defence.

-   **Hidden coupling.** Each change can pass its tests while quietly
    adding dependencies that make later changes fragile. The
    pressure-field paper flags this; shapers and periodic whole-system
    checks must catch it.

-   **Risk-averse swarms.** Cursor\'s flat agents avoided hard problems.
    Pressure has to build on neglected hard regions until a stronger
    model takes them.

-   **Architecture drift.** With no central designer, the design may
    wander. The brain\'s record of decisions and the shapers are the
    bet, and that bet is unproven.

-   **Irreducible coupling.** Some work is inherently sequential; Google
    measured 39--70% losses there. Hive should detect it and run few
    agents on that part.

-   **Safety.** Thousands of agents executing code need isolated
    sandboxes, spend limits, and a kill switch. Passing tests is not the
    same as verified software.

Open questions:

-   Can coupling be estimated before a run, from the code\'s dependency
    graph?

-   What half-life should memories and signals have, and should it adapt
    to progress?

-   Which interface changes may shapers make on their own, and which
    need human approval?

## Build plan

Grow the swarm only after each phase passes its gate. The wind tunnel
comes first because it decides whether the rest is worth building.

![Build plan · 4 phases, each with a
gate](media/image3.png){width="6.0in" height="2.1696423884514435in"}

Build plan · 4 phases, each with a gate

Every phase reuses the wind-tunnel project, so each gate is measured the
same way. If a gate fails, fix the design before adding agents.

## Sources

-   [Towards a science of scaling agent
    systems](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/),
    Google Research, Jan 2026

-   [Building a C compiler with a team of parallel
    Claudes](https://www.anthropic.com/research/building-c-compiler),
    Anthropic, Feb 2026

-   [Scaling long-running autonomous
    coding](https://cursor.com/blog/scaling-agents), Cursor, Jan 2026

-   [Emergent coordination via pressure fields and temporal
    decay](https://arxiv.org/abs/2601.08129), Rodriguez, Jan 2026

-   [CodeCRDT: observation-driven coordination for multi-agent code
    generation](https://arxiv.org/abs/2510.18893), Pugachev, Oct 2025

-   [Why do multi-agent LLM systems
    fail?](https://arxiv.org/abs/2503.13657), UC Berkeley, 2025

-   [Stigmergy
    Swarm](https://docs.codebolt.ai/docs/concepts/multi-agent/stigmergy-swarm),
    Codebolt docs

-   [dot_swarm](https://pypi.org/project/dot-swarm/) and
    [Anthills](https://pypi.org/project/anthills/), PyPI
