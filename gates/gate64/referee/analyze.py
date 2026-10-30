"""G64 registered analysis (committed with the predictions, before any team runs). Run from the repo root:
    python3 gates/gate64/referee/analyze.py runs/g64
t95 / tdone = minutes from the team's start (the lead's start for OH, OHE) to the first landing after which >= 95% /
100% of visible tests pass (inf if never); cost = every builder of every wave plus the lead; hidden pass as in Gate 50
(local-SQLite-disagreeing categories left out).
D1  H reaches 1,340 visible                       D2  OH's t95 <= 0.8 x H's (or H never reaches 95%)
D3  HE finishes (1,340), hidden within 1 point of S, cost <= 0.6 x S
D4  OHE the same                                  D5  OHE costs at least HE
Cheap pace = Haiku + escalation: D3 holds. The Opus planner too: D4 holds and OHE beats HE by >= 15% on cost or tdone.
Kill: neither HE nor OHE finishes at <= 0.6 x S's cost (Sonnet builders stay)."""
import collections, csv, glob, json, math, os, re, sqlite3, sys

d = sys.argv[1]
teams = json.load(open(os.path.join(d, 'teams.json')))
rows = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))):
    rows[re.sub(r'x\d+$', '', r['worker'].split('-w')[0])].append(r)
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
    first = lambda k: (min(p['t'] for p in prog if p['visible'] >= k) - t0) / 60 if any(p['visible'] >= k for p in prog) else math.inf
    h = {k: ok for k, ok in v['hidden'].items() if cat(k) not in bad}
    by_model = collections.Counter()
    for r in rows[team]:
        by_model['sonnet' if 'x1' in r['worker'] else 'opus' if 'x2' in r['worker'] else 'first'] += float(r['cost_usd'] or 0)
    lead = v.get('lead_cost') or 0
    R[team] = dict(t95=first(1273), tdone=first(1340), visible=sum(v['visible'].values()),
                   hidden=100 * sum(h.values()) / len(h) if h else float('nan'), lead=lead, builders=dict(by_model),
                   cost=sum(by_model.values()) + lead, waves=len(v.get('waves') or []),
                   breaks=sum(1 for a, b in zip(prog, prog[1:]) if b['visible'] < a['visible'] - 20))
print(f'hidden categories left out: {sorted(bad)}')
print('team  t95(min)  tdone(min)  visible  hidden   cost   (first wave / sonnet / opus / lead)  escalation waves  breaks')
for t, r in R.items():
    b = r['builders']
    print(f"{t:4s}  {r['t95']:7.1f}   {r['tdone']:7.1f}    {r['visible']:5d}  {r['hidden']:5.1f}%  ${r['cost']:5.2f}  "
          f"({b.get('first', 0):.2f} / {b.get('sonnet', 0):.2f} / {b.get('opus', 0):.2f} / {r['lead']:.2f})   {r['waves']}   {r['breaks']}")
S, H, OH, HE, OHE = (R[k] for k in ('S', 'H', 'OH', 'HE', 'OHE'))
ok = lambda X: X['tdone'] < math.inf and abs(X['hidden'] - S['hidden']) <= 1 and X['cost'] <= .6 * S['cost']
res = [('D1', f"H reaches 1,340 visible: {H['visible']}", H['visible'] >= 1340),
       ('D2', f"OH t95 ≤ 0.8 × H's: {OH['t95']:.1f} vs {H['t95']:.1f}", OH['t95'] <= .8 * H['t95'] or (H['t95'] == math.inf and OH['t95'] < math.inf)),
       ('D3', f"HE finishes, hidden within 1 of S, cost ≤ 0.6 × S: tdone {HE['tdone']:.1f}, hidden {HE['hidden']:.1f} vs {S['hidden']:.1f}, "
              f"cost {HE['cost'] / S['cost']:.2f}× S", ok(HE)),
       ('D4', f"OHE the same: tdone {OHE['tdone']:.1f}, hidden {OHE['hidden']:.1f}, cost {OHE['cost'] / S['cost']:.2f}× S", ok(OHE)),
       ('D5', f"OHE costs ≥ HE: ${OHE['cost']:.2f} vs ${HE['cost']:.2f}", OHE['cost'] >= HE['cost'])]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
better = OHE['cost'] <= .85 * HE['cost'] or OHE['tdone'] <= .85 * HE['tdone']
print(f"Cheap pace = Haiku + escalation: {'FIRED' if ok(HE) else 'did not fire'}")
print(f"The Opus planner too: {'FIRED' if ok(OHE) and better else 'did not fire'}")
print(f"Kill (Sonnet builders stay): {'FIRED' if not ok(HE) and not ok(OHE) else 'did not fire'}")
