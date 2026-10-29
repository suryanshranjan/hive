"""G51 registered analysis (committed with the predictions, before any team runs). Run from the repo root:
    python3 gates/gate51/referee/analyze.py runs/g51
t95, cost, hidden and breaks as in Gate 50; load = mean 1-minute load average while the team ran (2 cores).
S = mean of S1, S2; T = mean of T1, T2.
F1: notes do not speed 12 builders up by ≥ 15% (t95_T > 0.85 × t95_S).     F2: cost within ±10%.
F3: the machine is saturated while 12 builders run: mean load ≥ 2.0 on 2 cores.   F4: each notes team posts ≥ 5 notes.
Keep notes at 10+ builders: t95_T ≤ 0.85 × t95_S in both pairings (T1/S1, T2/S2), cost ≤ 1.10×.
Turn the size trigger off: T not faster (t95_T ≥ t95_S) — notes then switch on only on frequent collisions."""
import collections, csv, glob, json, os, sqlite3, sys

d = sys.argv[1]
teams = json.load(open(os.path.join(d, 'teams.json')))
rows = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): rows[r['worker'].split('-w')[0]].append(r)
bad = {'median', 'percentile'}
def norm(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool): return ('n', round(float(v), 6))
    return ('0',) if v is None else ('s', str(v))
for f in glob.glob(os.path.join(d, 'seed_S', 'tests', 'visible', '*.json')):
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
    loads = [l for _, l in v['load']]
    R[team] = dict(t95=(min(p['t'] for p in hit) - t0) / 60 if hit else float('inf'), landings=len(prog),
                   breaks=sum(1 for a, b in zip(prog, prog[1:]) if b['visible'] < a['visible'] - 20),
                   hidden=100 * sum(h.values()) / len(h) if h else float('nan'), notes=v['notes'],
                   cost=sum(float(r['cost_usd'] or 0) for r in rows[team]), load=sum(loads) / len(loads) if loads else float('nan'),
                   peak=max(loads) if loads else float('nan'))
print('team  t95(min)  landings  breaks  notes  hidden   cost    mean load (peak)')
for t in ('S1', 'T1', 'T2', 'S2'):
    r = R[t]
    print(f'{t:4s} {r["t95"]:7.1f}   {r["landings"]:5d}   {r["breaks"]:4d}   {r["notes"]:4d}  {r["hidden"]:6.1f}%  ${r["cost"]:5.2f}   {r["load"]:5.1f} ({r["peak"]:.1f})')
m = lambda k, a: (R[a + '1'][k] + R[a + '2'][k]) / 2
tS, tT, cS, cT = m('t95', 'S'), m('t95', 'T'), m('cost', 'S'), m('cost', 'T')
print(f'\nmeans: t95 S {tS:.1f} vs T {tT:.1f} (ratio {tT / tS:.2f}); cost S ${cS:.2f} vs T ${cT:.2f} (ratio {cT / cS:.2f}); load S {m("load", "S"):.1f} vs T {m("load", "T"):.1f}')
print('\npredictions')
for tag, text, held in [
        ('F1', f'notes not ≥ 15% faster: ratio {tT / tS:.2f}', tT > .85 * tS),
        ('F2', f'cost within ±10%: {cT / cS:.2f}', .9 <= cT / cS <= 1.1),
        ('F3', f'mean load ≥ 2.0: {min(r["load"] for r in R.values()):.1f}–{max(r["load"] for r in R.values()):.1f}', min(r['load'] for r in R.values()) >= 2.0),
        ('F4', f'each notes team ≥ 5 notes: {R["T1"]["notes"]}, {R["T2"]["notes"]}', min(R['T1']['notes'], R['T2']['notes']) >= 5)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
keep = all(R[a]['t95'] <= .85 * R[b]['t95'] for a, b in (('T1', 'S1'), ('T2', 'S2'))) and cT <= 1.1 * cS
print(f'Keep notes at 10+ builders: {"FIRED" if keep else "did not fire"}')
print(f'Turn the size trigger off (notes not faster): {"FIRED" if tT >= tS else "did not fire"}')
