"""G46 registered analysis (committed with the predictions, before any team runs). Run from the repo root:
    python3 gates/gate46/referee/analyze.py runs/g46
Per team (time from the team's start: the lead's start for H, the workers' for F):
t95 = first landing after which ≥ 95% of visible tests (1,273 of 1,340) pass; v10, v20 = visible passing at 10 and 20
minutes; finish = last landing by a worker; cost = workers + lead; hidden pass on gen2's suite without categories where
this SQLite disagrees with the stored visible answers (Gate 43's rule). F = mean of F1, F2; H = mean of H1, H2.
D1: each lead's plan is on main within 6 minutes.        D2: H is not ≥ 20% sooner to 95% (t95_H > 0.8 × t95_F).
D3: H costs ≥ 1.10 × F.                                   D4: at 10 minutes H has fewer tests passing than F.
D5: final hidden pass within 3 points.
Ship (lead + brain mode in Hive for deep projects): t95_H ≤ 0.8 × t95_F in both pairings (H1/F1, H2/F2), cost ≤ 1.15×.
Kill: t95_H ≥ t95_F and cost_H > cost_F."""
import collections, csv, glob, json, os, sqlite3, sys

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
    t0 = v['team_start']; prog = [p for p in v['progress'] if p['visible'] is not None]
    def at(minute):
        ok = [p['visible'] for p in prog if p['t'] - t0 <= minute * 60]
        return max(ok) if ok else 9
    hit = [p for p in prog if p['visible'] >= 1273]
    t95 = (min(p['t'] for p in hit) - t0) / 60 if hit else float('inf')
    work = [p for p in prog if not p['subject'].startswith('BRAIN') and not p['who'].endswith('-lead')]
    finish = (max(p['t'] for p in work) - t0) / 60 if work else float('nan')
    h = {k: ok for k, ok in v['hidden'].items() if cat(k) not in bad}
    wc = sum(float(r['cost_usd'] or 0) for r in rows[team])
    ev = collections.Counter()
    for lg in glob.glob(os.path.join(d, 'logs', f'{team}-w*.log')):
        for line in open(lg):
            p = line.split()
            if len(p) > 1: ev[p[1]] += 1
    R[team] = dict(t95=t95, v10=at(10), v20=at(20), finish=finish, visible=sum(v['visible'].values()),
                   hidden=100 * sum(h.values()) / len(h) if h else float('nan'), workers_cost=wc,
                   cost=wc + (v.get('lead_cost') or 0), lead_cost=v.get('lead_cost'), plan=v.get('plan_seconds'),
                   landings=len(work), brain_updates=sum(p['subject'].startswith('BRAIN') for p in prog),
                   conflicts=ev['CONFLICT'], blocks=ev['BLOCKED_DUP'] + ev['BLOCKED_REGRESSION'], logged=ev['LAND'])
print(f'hidden categories left out: {sorted(bad)}')
print('team  t95(min)  v10   v20   finish  visible  hidden  cost(lead)      plan(s)  landings  brain  conflicts blocks logged')
for t in ('F1', 'H1', 'H2', 'F2'):
    r = R[t]; lead = '–' if r['lead_cost'] is None else f"${r['lead_cost']:.2f}"
    print(f'{t:4s} {r["t95"]:7.1f}  {r["v10"]:4d}  {r["v20"]:4d}  {r["finish"]:6.1f}  {r["visible"]:5d}  {r["hidden"]:6.1f}%  '
          f'${r["cost"]:5.2f} ({lead})  {str(r["plan"]):>6}  '
          f'{r["landings"]:6d}  {r["brain_updates"]:4d}  {r["conflicts"]:5d}  {r["blocks"]:5d}  {r["logged"]:5d}')
m = lambda k, a: (R[a + '1'][k] + R[a + '2'][k]) / 2
tF, tH, cF, cH = m('t95', 'F'), m('t95', 'H'), m('cost', 'F'), m('cost', 'H')
print(f'\nmeans: t95 F {tF:.1f} vs H {tH:.1f} min (ratio {tH / tF:.2f}); cost F ${cF:.2f} vs H ${cH:.2f} (ratio {cH / cF:.2f}); '
      f'v10 F {m("v10", "F"):.0f} vs H {m("v10", "H"):.0f}; hidden F {m("hidden", "F"):.1f} vs H {m("hidden", "H"):.1f}')
print('\npredictions')
for tag, text, held in [
        ('D1', f'plans within 6 min: {R["H1"]["plan"]} s, {R["H2"]["plan"]} s', max(R['H1']['plan'] or 1e9, R['H2']['plan'] or 1e9) <= 360),
        ('D2', f'H not ≥ 20% sooner to 95%: ratio {tH / tF:.2f}', tH > .8 * tF),
        ('D3', f'H costs ≥ 1.10× F: {cH / cF:.2f}', cH >= 1.1 * cF),
        ('D4', f'at 10 min H < F: {m("v10", "H"):.0f} vs {m("v10", "F"):.0f}', m('v10', 'H') < m('v10', 'F')),
        ('D5', f'hidden within 3 points: {m("hidden", "H") - m("hidden", "F"):+.1f}', abs(m('hidden', 'H') - m('hidden', 'F')) <= 3)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
ship = all(R[h]['t95'] <= .8 * R[f]['t95'] for h, f in (('H1', 'F1'), ('H2', 'F2'))) and cH <= 1.15 * cF
print(f'Ship (lead + brain ≥ 20% sooner in both pairings, cost ≤ 1.15×): {"FIRED" if ship else "did not fire"}')
print(f'Kill (not sooner and costlier): {"FIRED" if tH >= tF and cH > cF else "did not fire"}')
