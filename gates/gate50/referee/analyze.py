"""G50 registered analysis (committed with the predictions, before any team runs). Run from the repo root:
    python3 gates/gate50/referee/analyze.py runs/g50
t95 = minutes from the team's start to the first landing after which ≥ 95% of visible tests (1,273 of 1,340) pass
(inf if never); cost = all builders; hidden pass as in Gate 46 (local-SQLite-disagreeing categories left out).
Speedup S(N) = t95(N1) / t95(N). A universal scalability law S(N) = N / (1 + σ(N−1) + κN(N−1)) is fitted by grid search.
E1: one builder reaches 95% within 90 minutes.          E2: S(7) ≥ 2.0.
E3: 12 builders are not > 10% faster than 7 (t95(N12) ≥ 0.9 × t95(N7)).
E4: cost(N7) ≤ 1.5 × cost(N1).                           E5: hidden pass of every team within 1 point of the others.
Rule: S(7) < 1.25 → with today's model the swarm barely beats one agent; the law should pick far fewer builders."""
import collections, csv, glob, json, math, os, sqlite3, sys

d = sys.argv[1]
teams = json.load(open(os.path.join(d, 'teams.json')))
rows = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): rows[r['worker'].split('-w')[0]].append(r)
bad = {'median', 'percentile'}
def norm(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool): return ('n', round(float(v), 6))
    return ('0',) if v is None else ('s', str(v))
for f in glob.glob(os.path.join(d, 'seed', 'tests', 'visible', '*.json')):
    t = json.load(open(f))
    try:
        c = sqlite3.connect(':memory:')
        for s in t.get('setup', []): c.execute(s)
        got = [tuple(norm(v) for v in r) for r in c.execute(t['query']).fetchall()]
        exp = [tuple(norm(v) for v in r) for r in t['expected']]
        if (got if t.get('ordered') else sorted(got)) != (exp if t.get('ordered') else sorted(exp)): bad.add(t['category'])
    except Exception:
        bad.add(t['category'])
cat = lambda tid: tid.rsplit('_', 1)[0]
R = {}
for team, v in teams.items():
    t0 = v['team_start']; prog = [p for p in v['progress'] if p['visible'] is not None and p['t'] >= t0 - 5]
    hit = [p for p in prog if p['visible'] >= 1273]
    h = {k: ok for k, ok in v['hidden'].items() if cat(k) not in bad}
    R[team] = dict(n=v['builders'], t95=(min(p['t'] for p in hit) - t0) / 60 if hit else float('inf'),
                   last=(max(p['t'] for p in prog) - t0) / 60 if prog else float('nan'), landings=len(prog),
                   breaks=sum(1 for a, b in zip(prog, prog[1:]) if b['visible'] < a['visible'] - 20),
                   visible=sum(v['visible'].values()), hidden=100 * sum(h.values()) / len(h) if h else float('nan'),
                   cost=sum(float(r['cost_usd'] or 0) for r in rows[team]),
                   tokens=sum(int(r['tokens'] or 0) for r in rows[team]))
order = sorted(R, key=lambda t: R[t]['n'])
base = R['N1']['t95']
print(f'hidden categories left out: {sorted(bad)}')
print('team  N   t95(min)  speedup  efficiency  last landing  landings  breaks  visible  hidden   cost    cost/N1')
for t in order:
    r = R[t]; s = base / r['t95'] if r['t95'] not in (0, float('inf')) else float('nan')
    print(f'{t:4s} {r["n"]:2d}  {r["t95"]:7.1f}  {s:6.2f}   {s / r["n"]:6.2f}     {r["last"]:7.1f}     {r["landings"]:5d}   {r["breaks"]:4d}   '
          f'{r["visible"]:5d}  {r["hidden"]:6.1f}%  ${r["cost"]:5.2f}  {r["cost"] / R["N1"]["cost"]:5.2f}x')
pts = [(R[t]['n'], base / R[t]['t95']) for t in order if R[t]['t95'] not in (0, float('inf'))]
best = None
for i in range(0, 101):
    for j in range(0, 101):
        sg, kp = i / 100, j / 1000
        err = sum((math.log(s) - math.log(n / (1 + sg * (n - 1) + kp * n * (n - 1)))) ** 2 for n, s in pts)
        if best is None or err < best[0]: best = (err, sg, kp)
_, sg, kp = best
nstar = math.sqrt((1 - sg) / kp) if kp > 0 else float('inf')
print(f'\nUSL fit: σ (serial share) = {sg:.2f}, κ (crosstalk) = {kp:.3f}; peak speedup at N* ≈ {nstar:.1f} builders')
print('\npredictions')
s7 = base / R['N7']['t95'] if R['N7']['t95'] not in (0, float('inf')) else float('nan')
for tag, text, held in [
        ('E1', f'one builder reaches 95% within 90 min: {R["N1"]["t95"]:.1f} min', R['N1']['t95'] <= 90),
        ('E2', f'S(7) ≥ 2.0: {s7:.2f}', s7 >= 2.0),
        ('E3', f'12 not > 10% faster than 7: {R["N12"]["t95"]:.1f} vs {R["N7"]["t95"]:.1f}', R['N12']['t95'] >= .9 * R['N7']['t95']),
        ('E4', f'cost N7 ≤ 1.5 × N1: {R["N7"]["cost"] / R["N1"]["cost"]:.2f}×', R['N7']['cost'] <= 1.5 * R['N1']['cost']),
        ('E5', f'hidden within 1 point: {min(r["hidden"] for r in R.values()):.1f}–{max(r["hidden"] for r in R.values()):.1f}',
         max(r['hidden'] for r in R.values()) - min(r['hidden'] for r in R.values()) <= 1)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Rule S(7) < 1.25 (swarm barely beats one agent): {"FIRED" if s7 < 1.25 else "did not fire"}')
