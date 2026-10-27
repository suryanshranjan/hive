"""G13 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python gate13/referee/analyze.py gate13/results
fixed_X = edge calls right in team X minus right in N0, summed over all functions.
M1: fixed_T / fixed_Q (bootstrap over functions).   M2: share of N0's edge errors fixed by TQ.
M3: reach. Of edge calls wrong in both N0 and Q, the share right in T.
M4: questions used by Q and TQ (budget 17 each).   M5: N0 hidden pass (from summary.json)."""
import gzip, json, os, random, sys

d = sys.argv[1]
P = {a: json.load(gzip.open(os.path.join(d, f'probe_{a}.json.gz'))) for a in ('N0', 'T', 'Q', 'TQ')}
key = lambda r: (r['cat'], r['test'], r['q'])
edge = {a: {key(r): r['ok'] for r in P[a] if r['kind'] == 'edge'} for a in P}
cats = sorted({k[0] for k in edge['N0']})
right = {a: {c: sum(v for k, v in edge[a].items() if k[0] == c) for c in cats} for a in P}
E = {c: sum(1 for k, v in edge['N0'].items() if k[0] == c and not v) for c in cats}
fixed = {a: {c: right[a][c] - right['N0'][c] for c in cats} for a in ('T', 'Q', 'TQ')}

def ratio(cs, a='T', b='Q'):
    den = sum(fixed[b][c] for c in cs)
    return sum(fixed[a][c] for c in cs) / den if den else float('inf')

rnd = random.Random(7)
bs = sorted(ratio([rnd.choice(cats) for _ in cats]) for _ in range(4000))
tot = sum(E.values())
print(f'N0 edge errors {tot}; fixed: ' + ', '.join(f'{a} {sum(fixed[a].values())} ({sum(fixed[a].values()) / tot:.2f})' for a in fixed))
print(f'M1 T/Q = {ratio(cats):.3f}  (95% CI {bs[100]:.3f} to {bs[3899]:.3f}, bootstrap over functions)')
print(f'M2 TQ share fixed = {sum(fixed["TQ"].values()) / tot:.3f}')
both = [k for k, v in edge['N0'].items() if not v and not edge['Q'][k]]
print(f'M3 reach: of {len(both)} edge calls wrong in N0 and Q, T gets {sum(edge["T"][k] for k in both) / len(both):.3f} right, '
      f'TQ {sum(edge["TQ"][k] for k in both) / len(both):.3f}')
for a in ('Q', 'TQ'):
    print(f'M4 questions used {a}:', sum(1 for l in open(os.path.join(d, f'asks_{a}.log')) if json.loads(l).get('charged')), 'of 17')
s = json.load(open(os.path.join(d, 'summary.json')))
print('M5 hidden pass: ' + ', '.join(f'{a} {v["hidden_pass"]:.1%}' for a, v in s['arms'].items()))
print('per function: N0 errors, fixed by T / Q / TQ')
for c in cats:
    print(f'  {c:24s} E={E[c]:3d}  {fixed["T"][c]:+4d} / {fixed["Q"][c]:+4d} / {fixed["TQ"][c]:+4d}')
