"""How many builders: Hive's swarm law, with this project's own numbers.

    useful work per minute  X(N) = min( N(1−f) / (τ·(1 + κd(N−1))),   (1−f) / (r·t_g),   I/b )

- Coupling: each pair of concurrent builders collides on the same lines with share κ, and a collision costs d of a
  task. Measured: κ = 0.049, d = 0.27 (BRAIN §4), so κd ≈ 0.013. This barely binds below about 20 builders.
- Gate: every landing runs the full test suite about r = 2 times (Gates 21-22), so landings are capped at 1/(r·t_g),
  t_g being this project's suite time, measured before each build. A builder lands about every τ = 5 minutes, so more
  than τ/(r·t_g) builders only queue at the guard.
- Hardware: about one CPU core per builder (Gate 21: 3.5 minutes on 24 cores, 12.1 on 4, same 12-builder job).
- Work: about 3 business decisions per builder. Each builder costs about 110k tokens just to get started (Gates 1-3),
  so a small job does not pay for many builders.
- Intent (I/b) is not limited by builder count; the interview sets it.
Status: the terms are measured; using their minimum to pick N is a model, not yet a held-out prediction."""
import math, os

KAPPA, D = 0.049, 0.27
TAU_MIN, RUNS_PER_LANDING = 5.0, 2.0
DECISIONS_PER_BUILDER = 3
CAP = 8   # the largest swarm measured end to end on a real codebase (Gates 24-25)

def throughput(n, t_g_min):
    """Landings per minute with n builders and a suite of t_g_min minutes (model)."""
    coupling = n / (TAU_MIN * (1 + KAPPA * D * (n - 1)))
    gate = 1 / (RUNS_PER_LANDING * max(t_g_min, 1e-6))
    return min(coupling, gate)

def builders(t_g_seconds, cpus=None, decisions=None, cap=CAP):
    """(N, why): the number of builders for this project, and which limit set it, in plain words."""
    cpus = cpus or os.cpu_count() or 2
    t_g = max(t_g_seconds, 1) / 60
    limits = {
        'your test suite': max(1, math.floor(TAU_MIN / (RUNS_PER_LANDING * t_g))),
        'this computer': max(1, cpus),
        'the largest swarm tested on a real codebase': cap,
    }
    if decisions:
        limits['the size of the job'] = max(1, math.ceil(decisions / DECISIONS_PER_BUILDER))
    # coupling: stop where one more builder adds under 5% more landings
    n_coupling = 1
    while n_coupling < 64 and throughput(n_coupling + 1, t_g) > 1.05 * throughput(n_coupling, t_g):
        n_coupling += 1
    limits['builders getting in each other\'s way'] = n_coupling
    why = min(limits, key=lambda k: limits[k])
    n = max(1, min(limits.values()))
    secs = round(t_g_seconds)
    detail = {'your test suite': f'your tests take {secs} s, and every landing runs them about twice',
              'this computer': f'this computer has {cpus} cores, about one per builder',
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
