"""G12 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python gate12/referee/analyze.py gate12/results gate12/referee/oracle.py
share_q(f) = (edge calls right in team Qq − right in N0) / N0's edge errors, for functions with N0 edge errors ≥ 5.
D1: mean share_1 over functions with d ∈ {1,2} minus over d ∈ {3,4}.
D2: Spearman ρ between d and q* = smallest q ∈ {1,2,4} with share_q ≥ 0.8 · max(share_1, share_2, share_4),
    over functions whose best share is > 0.
D3: pooled share (errors fixed / errors) at Q1 ≤ Q2 ≤ Q4.  D4: pooled share at Q4 ≥ 0.80."""
import gzip, importlib.util, json, os, sys

d, oracle = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('oracle', oracle); o = importlib.util.module_from_spec(spec); spec.loader.exec_module(o)
DEC = {f: len(v) for f, v in o.DECISIONS.items()}

def right(arm):
    p = os.path.join(d, f'probe_{arm}.json.gz')
    out = {}
    for r in json.load(gzip.open(p)):
        if r['kind'] == 'edge':
            out.setdefault(r['cat'], []).append(r['ok'])
    return {c: (sum(v), len(v)) for c, v in out.items()}

base = right('N0'); arms = {q: right(f'Q{q}') for q in (1, 2, 4)}
E = {c: n - r for c, (r, n) in base.items()}
fx = {q: {c: arms[q][c][0] - base[c][0] for c in base} for q in arms}
fs = [c for c in base if E[c] >= 5]
share = {c: {q: fx[q][c] / E[c] for q in arms} for c in fs}

def rank(xs):
    s = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and xs[s[j + 1]] == xs[s[i]]: j += 1
        for k in range(i, j + 1): r[s[k]] = (i + j) / 2
        i = j + 1
    return r

def spearman(a, b):
    ra, rb = rank(a), rank(b); n = len(a); ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** .5
    return num / den if den else 0.0

lo = [share[c][1] for c in fs if DEC[c] <= 2]; hi = [share[c][1] for c in fs if DEC[c] >= 3]
D1 = sum(lo) / len(lo) - sum(hi) / len(hi)
keep = [c for c in fs if max(share[c].values()) > 0]
qstar = {c: min(q for q in (1, 2, 4) if share[c][q] >= 0.8 * max(share[c].values())) for c in keep}
rho = spearman([DEC[c] for c in keep], [qstar[c] for c in keep])
pooled = {q: sum(fx[q][c] for c in base) / sum(E.values()) for q in arms}
print(f'functions with N0 edge errors >= 5: {len(fs)} of {len(base)}; decisions among them: '
      + ', '.join(f'{k}:{sum(1 for c in fs if DEC[c] == k)}' for k in (1, 2, 3, 4)))
print(f'D1 share at 1 question, d<=2 minus d>=3: {D1:+.3f}  ({len(lo)} vs {len(hi)} functions)')
print(f'D2 Spearman rho(d, q*): {rho:+.3f}  ({len(keep)} functions)')
print('D3/D4 pooled share fixed: ' + ', '.join(f'Q{q} {v:.3f}' for q, v in pooled.items()))
print('mean share by decisions (q = 1 / 2 / 4):')
for k in (1, 2, 3, 4):
    g = [c for c in fs if DEC[c] == k]
    if g: print(f'  d={k}: ' + ' / '.join(f'{sum(share[c][q] for c in g) / len(g):+.2f}' for q in (1, 2, 4)) + f'  ({len(g)} functions)')
print('per function: d, N0 errors, share at 1 / 2 / 4, q*')
for c in sorted(base, key=lambda c: (DEC[c], c)):
    s = ' / '.join(f'{fx[q][c] / E[c]:+.2f}' if E[c] else '  n/a' for q in (1, 2, 4))
    print(f'  {c:24s} d={DEC[c]}  E={E[c]:3d}  {s}  q*={qstar.get(c, "-")}')
