"""G17 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python gate17/referee/analyze.py gate17/results gate17/referee/oracle.py
Probes are already filtered by run_gate.py: calls equal to an extractor pick are removed for every team (fair copy rule).
hp_X = hidden pass of team X (points). Paired differences: 95% intervals bootstrapped over functions.
F1: X − N0 ≥ +30.   F2: TQ − HXQ ≥ +5.   F3: HXQ ≥ 85.   F4: TQ ≥ 92.   F6: N0 below 70.
Share fixed = N0 edge errors right in team X / N0 edge errors, split by whether the function has an omitted decision."""
import collections, gzip, importlib.util, json, os, random, sys

d, oracle = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('oracle', oracle); o = importlib.util.module_from_spec(spec); spec.loader.exec_module(o)
arms = ('N0', 'X', 'HXQ', 'TQ')
P = {a: json.load(gzip.open(os.path.join(d, f'probe_{a}.json.gz'))) for a in arms}
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

x = json.load(open(os.path.join(d, 'xtour_inputs.json')))
print(f'extracted tour: {sum(len(v) for v in x["picked"].values())} inputs kept, {len(x["dropped"])} dropped, '
      f'{len(x.get("overlap", []))} equal hidden inputs (removed from scoring for every team)')
print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in arms))
for tag, a, b in (('F1', 'X', 'N0'), ('F2', 'TQ', 'HXQ'), ('--', 'HXQ', 'N0'), ('--', 'TQ', 'N0'), ('--', 'HXQ', 'X')):
    m, lo, hi = diff(a, b); print(f'{tag} {a} − {b} = {m:+.1f} (95% CI {lo:+.1f} to {hi:+.1f})')
print(f'F3 HXQ = {hp["HXQ"]:.1f}%   F4 TQ = {hp["TQ"]:.1f}%   F6 N0 = {hp["N0"]:.1f}%')
status = o.HANDBOOK_STATUS; om = {f for f, v in status.items() if 'omitted' in v}
def share(a, fs):
    e = [k for k, v in ok['N0'].items() if not v and k[0] in fs]
    return (sum(ok[a][k] for k in e) / len(e) if e else float('nan')), len(e)
for a in ('X', 'HXQ', 'TQ'):
    s1, n1 = share(a, om); s0, n0 = share(a, set(status) - om)
    print(f'share fixed {a}: functions with an omitted decision {s1:.2f} ({n1} errors); without {s0:.2f} ({n0} errors)')
for a in ('HXQ', 'TQ'):
    print(f'F5 questions used {a}:', sum(1 for l in open(os.path.join(d, f'asks_{a}.log')) if json.loads(l).get('charged')), 'of 17')
