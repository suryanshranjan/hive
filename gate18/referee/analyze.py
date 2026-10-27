"""G18 registered analysis (committed with the predictions, before the run). Prints aggregates only: no function names,
inputs or outputs, because the rules are a real company's and stay private. Run on the private results folder:
    python gate18/referee/analyze.py <private results dir>
fixed_X = edge calls wrong in N0 and right in X.  R1: T − N0 ≥ +20.  R2: fixed_T / fixed_Q ≥ 1.3.  R3: TQ ≥ 75%.
R5: N0 below 70%.  Also: reach (of edge calls wrong in N0 and Q, share right in T) and calls broken (right in N0, wrong in X)."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'T', 'Q', 'TQ')
def load(a):
    p = os.path.join(d, f'probe_{a}.json')
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
P = {a: load(a) for a in arms}
hp = {a: 100 * v['hidden_pass'] for a, v in json.load(open(os.path.join(d, 'summary.json')))['arms'].items()}
key = lambda r: (r['cat'], r['test'], r['q'])
ok = {a: {key(r): r['ok'] for r in P[a] if r['kind'] == 'edge'} for a in arms}

def per_function(a):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P[a]: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in tests.values()) / len(tests) for c, tests in t.items()}
pf = {a: per_function(a) for a in arms}; cats = sorted(pf['N0']); rnd = random.Random(7)
def diff(a, b):
    v = [pf[a][c] - pf[b][c] for c in cats]
    bs = sorted(sum(rnd.choice(v) for _ in v) / len(v) for _ in range(4000))
    return 100 * sum(v) / len(v), 100 * bs[100], 100 * bs[3899]

E = [k for k, v in ok['N0'].items() if not v]
fixed = {a: sum(ok[a][k] for k in E) for a in ('T', 'Q', 'TQ')}
broken = {a: sum(1 for k, v in ok['N0'].items() if v and not ok[a][k]) for a in ('T', 'Q', 'TQ')}
print(f'{len(cats)} functions; N0 edge errors {len(E)}')
print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in arms))
for a, b in (('T', 'N0'), ('Q', 'N0'), ('TQ', 'N0'), ('T', 'Q'), ('TQ', 'T')):
    m, lo, hi = diff(a, b); print(f'{a} − {b} = {m:+.1f} (95% CI {lo:+.1f} to {hi:+.1f})')
print('edge errors fixed: ' + ', '.join(f'{a} {v} ({v / len(E):.2f})' for a, v in fixed.items()) + '; broken: ' + ', '.join(f'{a} {v}' for a, v in broken.items()))
print(f'R2 fixed_T / fixed_Q = {fixed["T"] / fixed["Q"]:.2f}' if fixed['Q'] else 'R2: Q fixed nothing')
both = [k for k in E if not ok['Q'][k]]
print(f'reach: of {len(both)} edge calls wrong in N0 and Q, T gets {sum(ok["T"][k] for k in both) / len(both):.2f} right' if both else 'reach: n/a')
for a in ('Q', 'TQ'):
    p = os.path.join(d, f'asks_{a}.log')
    print(f'questions used {a}:', sum(1 for l in open(p) if json.loads(l).get('charged')) if os.path.exists(p) else 'n/a', 'of 19')
