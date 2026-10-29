"""How many builders: Hive's swarm law, with this project's own numbers.

    useful work per minute  X(N) = min( N(1−f) / (τ·(1 + κd(N−1))),   (1−f) / (r·t_g),   I/b )

- Coupling: each pair of concurrent builders collides on the same lines with share κ, and a collision costs d of a
  task. Measured: κ = 0.049, d = 0.27 (BRAIN §4), so κd ≈ 0.013. This barely binds below about 20 builders.
- Gate: every landing runs the full test suite about r = 2 times (Gates 21-22), so landings are capped at 1/(r·t_g),
  t_g being this project's suite time, measured before each build. A builder lands about every τ = 5 minutes, so more
  than τ/(r·t_g) builders only queue at the guard.
- Hardware: a builder keeps a core busy only while it runs tests or its agent works: about AGENT_CORE + r_b·t_g of a
  core (r_b test runs a minute). Gate 50: with a 1.4 s suite, 7 builders on 2 cores were 3.0× faster than one; Gate 21:
  with a slower suite, 12 builders on 4 cores were 3.5× slower than on 24. (Model fitted to those two; the old rule,
  one core per builder, would have given 2 builders here, and 2 were only 1.16× faster than one.)
- Team size: Gate 50 fitted a universal scalability law to 1, 2, 4, 7 and 12 builders on a deep project: serial share
  σ = 0.25 (the foundation everything waits on), crosstalk κ = 0.013, peak near 7.6 builders; 12 were slower than 7.
  Seven builders were 3.0× faster than one for 1.9× the cost; four 2.0× for 1.9×; twelve 1.9× for 3.4×.
- Work: about 3 business decisions per builder. Each builder costs about 110k tokens just to get started (Gates 1-3),
  so a small job does not pay for many builders.
- Intent (I/b) is not limited by builder count; the interview sets it.
Status: the terms are measured; using their minimum to pick N is a model, not yet a held-out prediction."""
import math, os

KAPPA, D = 0.049, 0.27
TAU_MIN, RUNS_PER_LANDING = 5.0, 2.0
AGENT_CORE, RUNS_PER_BUILDER_MIN = 0.1, 3.0   # CPU per builder: its agent, plus its own test runs (model, Gates 21, 50)
SIGMA, KAPPA_USL = 0.25, 0.013                # Gate 50's scalability fit (deep project, today's model)
COST_VS_ONE = {1: 1.0, 2: 1.6, 4: 1.9, 7: 1.9, 12: 3.4}   # Gate 50: a team's cost against one builder's, measured
DECISIONS_PER_BUILDER = 3
CAP = 8   # the largest swarm measured end to end on a real codebase (Gates 24-25)

def throughput(n, t_g_min):
    """Landings per minute with n builders and a suite of t_g_min minutes (model)."""
    coupling = n / (TAU_MIN * (1 + KAPPA * D * (n - 1)))
    gate = 1 / (RUNS_PER_LANDING * max(t_g_min, 1e-6))
    return min(coupling, gate)

def core_share(t_g_min):
    """The share of one core a builder keeps busy: its agent plus its test runs, never more than a whole core."""
    return min(1.0, AGENT_CORE + RUNS_PER_BUILDER_MIN * t_g_min)

def speedup(n):
    """How many times faster than one builder (Gate 50's fit; model)."""
    return n / (1 + SIGMA * (n - 1) + KAPPA_USL * n * (n - 1))

def cost_vs_one(n):
    """A team's cost against one builder's, interpolated from Gate 50's measurements."""
    pts = sorted(COST_VS_ONE.items())
    if n >= pts[-1][0]:
        return pts[-1][1] * n / pts[-1][0]
    for (a, ca), (b, cb) in zip(pts, pts[1:]):
        if a <= n <= b:
            return ca + (cb - ca) * (n - a) / (b - a)
    return 1.0

def trade(n):
    """The owner's trade in plain words: speed and cost against one builder (Gate 50)."""
    if n <= 1:
        return 'one builder: the cheapest, and the slowest'
    return f'about {speedup(n):.1f}× the speed of one builder, for about {cost_vs_one(n):.1f}× the cost'

def builders(t_g_seconds, cpus=None, decisions=None, cap=CAP):
    """(N, why): the number of builders for this project, and which limit set it, in plain words."""
    cpus = cpus or os.cpu_count() or 2
    t_g = max(t_g_seconds, 1) / 60
    limits = {
        'your test suite': max(1, math.floor(TAU_MIN / (RUNS_PER_LANDING * t_g))),
        'this computer': max(1, math.floor(cpus / core_share(t_g))),
        'the largest swarm tested on a real codebase': cap,
    }
    if decisions:
        limits['the size of the job'] = max(1, math.ceil(decisions / DECISIONS_PER_BUILDER))
    # coupling: the team size where more builders stop adding speed (Gate 50's scalability fit)
    limits['builders getting in each other\'s way'] = max(range(1, 65), key=speedup)
    why = min(limits, key=lambda k: limits[k])
    n = max(1, min(limits.values()))
    secs = round(t_g_seconds)
    detail = {'your test suite': f'your tests take {secs} s, and every landing runs them about twice',
              'this computer': f'this computer has {cpus} cores, and each builder keeps about '
                               f'{core_share(t_g):.1f} of one busy',
              'the size of the job': f'the job has about {decisions} decisions, about {DECISIONS_PER_BUILDER} per builder',
              'the largest swarm tested on a real codebase': 'that is the most builders tested end to end so far',
              "builders getting in each other's way": 'more would mostly wait on each other'}[why]
    return n, f'{detail}'


# Team notes (a one-line message to the team, carried in a landing's commit). Gates 43-44: a message board changed
# nothing at 3-6 builders (finish 1.03x, cost 1.01x; +0 on top of the owner's rules), because builders rarely collided.
# Collisions grow with swarm size (conflicts per landing 0.14 / 0.33 / 0.48 at 2 / 6 / 12, Gates 2-3), so notes are
# switched on only where collisions are likely to matter. Both thresholds are conjectures, not yet tested.
NOTES_FROM_BUILDERS = 10        # above the largest swarms where silence was measured to be enough
NOTES_FROM_CONFLICT_RATE = 0.5  # this run's rebase conflicts per landing (Gate 3's 12-worker rate was 0.48)

def notes(n, conflicts=0, landings=0):
    """(on, why): whether builders should post and read team notes."""
    if n >= NOTES_FROM_BUILDERS:
        return True, f"{n} builders: at this size they start getting in each other's way"
    if landings >= 4 and conflicts / landings >= NOTES_FROM_CONFLICT_RATE:
        return True, f'{conflicts} collisions in {landings} landings: builders keep editing the same code'
    return False, f'{n} builders rarely collide; silence is enough (Gates 43-44)'
