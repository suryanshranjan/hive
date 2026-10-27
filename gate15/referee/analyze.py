"""G15 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python gate15/referee/analyze.py gate15/results gate15/referee/oracle.py
hp_X = hidden pass of team X (points). fixed_X = edge calls wrong in N0 and right in X.
X1: hp_X − hp_N0 ≥ 0.5 · (hp_T − hp_N0).   X2: hp_X ≥ hp_H.   X3: hp_T − hp_X ≥ +5.
X4: share of N0 edge errors fixed by X, functions with no omitted decision minus functions with ≥ 1 omitted, ≥ +0.15.
X5: the extracted tour has ≥ 40 inputs; every team passes its visible tests (checked separately).   X6: N0 below 70%."""
import gzip, importlib.util, json, os, sys

d, oracle = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('oracle', oracle); o = importlib.util.module_from_spec(spec); spec.loader.exec_module(o)
arms = ('N0', 'T', 'H', 'X')
P = {a: json.load(gzip.open(os.path.join(d, f'probe_{a}.json.gz'))) for a in arms}
key = lambda r: (r['cat'], r['test'], r['q'])
ok = {a: {key(r): r['ok'] for r in P[a] if r['kind'] == 'edge'} for a in arms}
hp = {a: 100 * v['hidden_pass'] for a, v in json.load(open(os.path.join(d, 'summary.json')))['arms'].items()}
status = o.HANDBOOK_STATUS
counts = {k: sum(v.count(k) for v in status.values()) for k in ('clear', 'vague', 'omitted')}
x = json.load(open(os.path.join(d, 'xtour_inputs.json')))
print('handbook status of the 50 decisions:', counts)
print(f'extracted tour: {sum(len(v) for v in x["picked"].values())} inputs kept, {len(x["dropped"])} dropped')
print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in arms))
gT, gX = hp['T'] - hp['N0'], hp['X'] - hp['N0']
print(f'X1 X − N0 = {gX:+.1f} against half of T − N0 = {gT / 2:+.1f}  (X keeps {gX / gT:.2f} of the tour gain)' if gT else 'X1 undefined')
print(f'X2 X − H = {hp["X"] - hp["H"]:+.1f}')
print(f'X3 T − X = {hp["T"] - hp["X"]:+.1f}')

def share(a, fs):
    e = [k for k, v in ok['N0'].items() if not v and k[0] in fs]
    return sum(ok[a][k] for k in e) / len(e) if e else float('nan'), len(e)

none_om = {f for f, v in status.items() if 'omitted' not in v}; some_om = set(status) - none_om
for a in ('T', 'H', 'X'):
    s0, n0 = share(a, none_om); s1, n1 = share(a, some_om)
    print(f'X4 {a}: share fixed, no omitted decision {s0:.2f} ({len(none_om)} functions, {n0} errors) vs ≥ 1 omitted {s1:.2f} ({len(some_om)} functions, {n1} errors): {s0 - s1:+.2f}')
print('per function: decisions (status), N0 edge errors, fixed by T / H / X')
for f in sorted(status):
    e = [k for k, v in ok['N0'].items() if not v and k[0] == f]
    tag = ''.join({'clear': 'c', 'vague': 'v', 'omitted': 'o'}[s] for s in status[f])
    print(f'  {f:24s} {tag:5s} {len(e):3d}   ' + ' / '.join(f'{sum(ok[a][k] for k in e):3d}' for a in ('T', 'H', 'X')))
