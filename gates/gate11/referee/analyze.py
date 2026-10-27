"""Independent check of G11's scoring, from the raw probes. Run from the repo root:
    python gates/gate11/referee/analyze.py gates/gate11/results
Recomputes R (errors fixed by S / by B), share fixed per allowance level, questions used, and p (P4):
least squares on errors fixed, errors fixed ≈ E·(1 − (1−p)^q), over S and B together."""
import gzip, json, os, random, sys

d = sys.argv[1]

def edge(arm):
    p = os.path.join(d, f'probe_{arm}.json.gz')
    rows = json.load(gzip.open(p)) if os.path.exists(p) else json.load(open(p[:-3]))
    out = {}
    for r in rows:
        if r['kind'] == 'edge':
            out.setdefault(r['cat'], []).append(r['ok'])
    return {c: (sum(v), len(v)) for c, v in out.items()}

e0, es, eb = edge('N0'), edge('S'), edge('B')
al = {a: json.load(open(os.path.join(d, f'allowance_{a}.json'))) for a in 'SB'}
pairs = json.load(open(os.path.join(d, 'pairs.json')))
E = {c: n - r for c, (r, n) in e0.items()}
fx = {'S': {c: es[c][0] - e0[c][0] for c in e0}, 'B': {c: eb[c][0] - e0[c][0] for c in e0}}

def R(ps):
    b = sum(fx['B'][c] for p in ps for c in p)
    return sum(fx['S'][c] for p in ps for c in p) / b if b else float('inf')

rnd = random.Random(7)
bs = sorted(R([rnd.choice(pairs) for _ in pairs]) for _ in range(4000))
print(f'R = S/B = {R(pairs):.3f}  (95% CI {bs[100]:.3f} to {bs[3899]:.3f}, bootstrap over pairs)')
print(f'errors fixed: S {sum(fx["S"].values())}, B {sum(fx["B"].values())}, of N0 edge errors {sum(E.values())}')
for a in 'SB':
    for q in sorted(set(al[a].values())):
        fs = [c for c in al[a] if al[a][c] == q]; e = sum(E[c] for c in fs)
        print(f'  {a} q={q}: {len(fs)} functions, N0 errors {e}, share fixed {sum(fx[a][c] for c in fs) / e if e else float("nan"):+.2f}')
for a in 'SB':
    used = sum(1 for l in open(os.path.join(d, f'asks_{a}.log')) if json.loads(l).get('charged'))
    print(f'questions used {a}: {used} of {sum(al[a].values())}')
obs = [(al[a][c], E[c], fx[a][c]) for a in 'SB' for c in e0 if al[a][c] > 0 and E[c] > 0]
fit = lambda rows: min((i / 1000 for i in range(1, 1000)), key=lambda p: sum((f - e * (1 - (1 - p) ** q)) ** 2 for q, e, f in rows))
p = fit(obs); pb = sorted(fit([rnd.choice(obs) for _ in obs]) for _ in range(1000))
print(f'p (S and B together) = {p:.2f}  (95% CI {pb[25]:.2f} to {pb[974]:.2f})')
print('pairs (hi, lo), N0 errors, fixed by S, fixed by B:')
for hi, lo in pairs:
    print(f'  {hi:24s} E {E[hi]:3d}  S {fx["S"][hi]:+4d}  B {fx["B"][hi]:+4d}   |  {lo:24s} E {E[lo]:3d}  S {fx["S"][lo]:+4d}  B {fx["B"][lo]:+4d}')
