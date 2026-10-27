"""G14 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python gates/gate14/referee/analyze.py gates/gate14/results
broken_X = edge calls right in N0 but wrong in X (over-generalization and churn); fixed_X = wrong in N0, right in X.
C1: T − N0 hidden pass ≥ +20 points.   C2: broken_TC ≤ 0.5 · broken_T (untestable if broken_T < 10).
C3: TC hidden pass ≥ T hidden pass.     C5: N0 below 70% hidden."""
import gzip, json, os, sys

d = sys.argv[1]
P = {a: json.load(gzip.open(os.path.join(d, f'probe_{a}.json.gz'))) for a in ('N0', 'T', 'TC')}
key = lambda r: (r['cat'], r['test'], r['q'])
ok = {a: {key(r): r['ok'] for r in P[a] if r['kind'] == 'edge'} for a in P}
s = json.load(open(os.path.join(d, 'summary.json')))['arms']
hp = {a: 100 * s[a]['hidden_pass'] for a in s}
res = {}
for a in ('T', 'TC'):
    res[a] = dict(fixed=sum(1 for k, v in ok['N0'].items() if not v and ok[a][k]),
                  broken=sum(1 for k, v in ok['N0'].items() if v and not ok[a][k]))
E = sum(1 for v in ok['N0'].values() if not v)
print(f'hidden pass: ' + ', '.join(f'{a} {v:.1f}%' for a, v in hp.items()))
print(f'N0 edge errors {E}; ' + '; '.join(f'{a}: fixed {r["fixed"]}, broken {r["broken"]}' for a, r in res.items()))
print(f'C1 T − N0 = {hp["T"] - hp["N0"]:+.1f} points')
b = res['T']['broken']
print(f'C2 broken TC / T = {res["TC"]["broken"]} / {b}' + (' (untestable: broken_T < 10)' if b < 10 else f' = {res["TC"]["broken"] / b:.2f}'))
print(f'C3 TC − T = {hp["TC"] - hp["T"]:+.1f} points')
cats = sorted({k[0] for k in ok['N0']})
print('per function: N0 edge errors; T fixed/broken; TC fixed/broken')
for c in cats:
    ks = [k for k in ok['N0'] if k[0] == c]
    f = lambda a, w: sum(1 for k in ks if ok['N0'][k] != w and ok[a][k] == w)
    print(f'  {c:24s} {sum(1 for k in ks if not ok["N0"][k]):3d}   {f("T", True):3d}/{f("T", False):3d}   {f("TC", True):3d}/{f("TC", False):3d}')
