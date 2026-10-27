"""G16 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python gate16/referee/analyze.py gate16/results gate16/referee/oracle.py
hp_X = hidden pass of team X (points). Share fixed = N0 edge errors that team X gets right / N0 edge errors.
S1: hp_HXQ ≥ 90.   S2: hp_HX − hp_X ≥ +3.   S3: hp_HXQ − hp_HX ≥ +3.   S4: hp_X − hp_N0 ≥ +25.
S5: on functions with ≥ 1 omitted decision, HXQ's share fixed ≥ 0.85.   S7: N0 below 70%.
Paired differences get 95% intervals bootstrapped over functions (hidden pass per function)."""
import collections, gzip, importlib.util, json, os, random, sys

d, oracle = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('oracle', oracle); o = importlib.util.module_from_spec(spec); spec.loader.exec_module(o)
arms = ('N0', 'X', 'HX', 'HXQ')
P = {a: json.load(gzip.open(os.path.join(d, f'probe_{a}.json.gz'))) for a in arms}
key = lambda r: (r['cat'], r['test'], r['q'])
ok = {a: {key(r): r['ok'] for r in P[a] if r['kind'] == 'edge'} for a in arms}
hp = {a: 100 * v['hidden_pass'] for a, v in json.load(open(os.path.join(d, 'summary.json')))['arms'].items()}

def per_function(a):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P[a]: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in tests.values()) / len(tests) for c, tests in t.items()}

pf = {a: per_function(a) for a in arms}; cats = sorted(pf['N0']); rnd = random.Random(7)
def diff(a, b):
    v = [pf[a][c] - pf[b][c] for c in cats]
    bs = sorted(sum(rnd.choice(v) for _ in v) / len(v) for _ in range(4000))
    return 100 * sum(v) / len(v), 100 * bs[100], 100 * bs[3899]

status = o.HANDBOOK_STATUS
x = json.load(open(os.path.join(d, 'xtour_inputs.json')))
print('handbook status:', {k: sum(v.count(k) for v in status.values()) for k in ('clear', 'vague', 'omitted')})
print(f'extracted tour: {sum(len(v) for v in x["picked"].values())} inputs kept, {len(x["dropped"])} dropped')
print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in arms))
print(f'S1 HXQ = {hp["HXQ"]:.1f}%')
for tag, a, b in (('S2', 'HX', 'X'), ('S3', 'HXQ', 'HX'), ('S4', 'X', 'N0')):
    m, lo, hi = diff(a, b); print(f'{tag} {a} − {b} = {m:+.1f} (95% CI {lo:+.1f} to {hi:+.1f})')

def share(a, fs):
    e = [k for k, v in ok['N0'].items() if not v and k[0] in fs]
    return (sum(ok[a][k] for k in e) / len(e) if e else float('nan')), len(e)

om = {f for f, v in status.items() if 'omitted' in v}
for a in ('X', 'HX', 'HXQ'):
    s1, n1 = share(a, om); s0, n0 = share(a, set(status) - om)
    print(f'S5 {a}: share fixed, functions with an omitted decision {s1:.2f} ({n1} errors); without {s0:.2f} ({n0} errors)')
if os.path.exists(os.path.join(d, 'asks_HXQ.log')):
    print('S6 questions used HXQ:', sum(1 for l in open(os.path.join(d, 'asks_HXQ.log')) if json.loads(l).get('charged')), 'of 17')
print('per function: status, N0 edge errors, fixed by X / HX / HXQ')
for f in sorted(status):
    e = [k for k, v in ok['N0'].items() if not v and k[0] == f]
    tag = ''.join({'clear': 'c', 'vague': 'v', 'omitted': 'o'}[s] for s in status[f])
    print(f'  {f:24s} {tag:5s} {len(e):3d}   ' + ' / '.join(f'{sum(ok[a][k] for k in e):3d}' for a in ('X', 'HX', 'HXQ')))
