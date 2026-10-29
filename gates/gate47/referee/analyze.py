"""G47 registered analysis (committed with the predictions, before any team runs). Run from the repo root:
    python3 gates/gate47/referee/analyze.py runs/g47
Per team (time from the team's start; for LX and LC, from the lead's start):
t95 = first landing after which >= 95% of visible tests (1,273 of 1,340) pass; finish = last worker landing;
breaks = landings after which visible fell by 20 or more tests from the commit before, each charged to its author's
agent; landings and breaks per agent; leftover locks on the final main; hidden pass on gen2's suite without categories
where this SQLite disagrees with the stored visible answers (Gate 43's rule). Claude cost in dollars; Codex in tokens
(it runs on the owner's ChatGPT plan, so it has no per-run price).
P1: M1 and M2 each reach 95% within 45 minutes.        P2: M1 and M2 each break main at most once.
P3: in M1 and M2 each agent lands >= 25% of the work.   P4: mean t95(M) <= 1.15 x mean(t95(C), t95(X)).
P5: t95(X) >= 1.2 x t95(C).                             P6: final hidden pass of all six teams within 3 points.
P7: the Codex lead's plan is on main within 6 minutes.  P8: t95(LX) within 20% of t95(LC).
Ship (mixed swarms supported in Hive's docs): P1 and P2 hold.
Kill (Hive warns against mixing): an M team does not reach 95%, or the M teams break main more than C and X together."""
import collections, csv, glob, json, os, sqlite3, sys

d = sys.argv[1]
teams = json.load(open(os.path.join(d, 'teams.json')))
rows = collections.defaultdict(list); agent = {}
for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))):
    rows[r['worker'].split('-w')[0]].append(r); agent[r['worker']] = r.get('agent') or 'claude'
for t, v in teams.items():
    if v.get('lead_agent'): agent[f'{t}-lead'] = v['lead_agent']
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
    hit = [p for p in prog if p['visible'] >= 1273]
    t95 = (min(p['t'] for p in hit) - t0) / 60 if hit else float('inf')
    work = [p for p in prog if not p['subject'].startswith('BRAIN') and not p['who'].endswith('-lead')]
    finish = (max(p['t'] for p in work) - t0) / 60 if work else float('nan')
    lands, breaks, prev = collections.Counter(), collections.Counter(), 9
    for p in prog:
        a = agent.get(p['who'], '?')
        if p in work: lands[a] += 1
        if p['visible'] <= prev - 20: breaks[a] += 1
        prev = p['visible']
    h = {k: ok for k, ok in v['hidden'].items() if cat(k) not in bad}
    cost = sum(float(r['cost_usd'] or 0) for r in rows[team] if (r.get('agent') or 'claude') == 'claude')
    cost += v.get('lead_cost') or 0 if v.get('lead_agent') == 'claude' else 0
    xtok = sum(int(r['tokens'] or 0) for r in rows[team] if r.get('agent') == 'codex')
    xtok += int(v.get('lead_tokens') or 0) if v.get('lead_agent') == 'codex' else 0
    R[team] = dict(t95=t95, finish=finish, visible=sum(v['visible'].values()), lands=lands, breaks=breaks,
                   hidden=100 * sum(h.values()) / len(h) if h else float('nan'), cost=cost, xtok=xtok,
                   plan=v.get('plan_seconds'), exits=collections.Counter(r['exit'] for r in rows[team]))
print(f'hidden categories left out: {sorted(bad)}')
print('team  t95(min)  finish  visible  hidden  claude$  codex tokens  landings by agent       breaks by agent  plan(s)  exits')
for t in teams:
    r = R[t]
    print(f'{t:4s} {r["t95"]:7.1f}  {r["finish"]:6.1f}  {r["visible"]:5d}  {r["hidden"]:6.1f}%  ${r["cost"]:5.2f}  '
          f'{r["xtok"]:11,d}  {str(dict(r["lands"])):22s}  {str(dict(r["breaks"])):15s}  {str(r["plan"]):>6}  {dict(r["exits"])}')
g = lambda t, k: R[t][k] if t in R else float('nan')
M = [t for t in ('M1', 'M2') if t in R]
tM = sum(g(t, 't95') for t in M) / max(1, len(M)); tC, tX = g('C', 't95'), g('X', 't95')
share = lambda t, a: R[t]['lands'][a] / max(1, sum(R[t]['lands'].values()))
nb = lambda t: sum(R[t]['breaks'].values())
hid = [R[t]['hidden'] for t in R]
print('\npredictions')
for tag, text, held in [
        ('P1', 'M teams reach 95% within 45 min: ' + ', '.join(f'{t} {g(t, "t95"):.1f}' for t in M), all(g(t, 't95') <= 45 for t in M)),
        ('P2', 'M teams break main at most once: ' + ', '.join(f'{t} {nb(t)}' for t in M), all(nb(t) <= 1 for t in M)),
        ('P3', 'each agent lands >= 25% in M: ' + ', '.join(f'{t} codex {share(t, "codex"):.0%}' for t in M),
         all(.25 <= share(t, 'codex') <= .75 for t in M)),
        ('P4', f'mean t95 M {tM:.1f} <= 1.15 x mean(C, X) {(tC + tX) / 2:.1f}', tM <= 1.15 * (tC + tX) / 2),
        ('P5', f't95 X {tX:.1f} >= 1.2 x C {tC:.1f}', tX >= 1.2 * tC),
        ('P6', f'hidden spread {max(hid) - min(hid):.1f} points', max(hid) - min(hid) <= 3),
        ('P7', f'Codex lead plan on main: {g("LX", "plan")} s', (g('LX', 'plan') or 1e9) <= 360),
        ('P8', f't95 LX {g("LX", "t95"):.1f} vs LC {g("LC", "t95"):.1f}', abs(g('LX', 't95') - g('LC', 't95')) <= .2 * g('LC', 't95'))]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
ship = all(g(t, 't95') <= 45 for t in M) and all(nb(t) <= 1 for t in M)
kill = any(g(t, 't95') == float('inf') for t in M) or sum(nb(t) for t in M) > nb('C') + nb('X')
print(f'Ship (mixed swarms supported): {"FIRED" if ship else "did not fire"}')
print(f'Kill (warn against mixing): {"FIRED" if kill else "did not fire"}')
