"""Gate 20 amendment, registered analysis for team HTQ (handbook + examples + questions). Aggregates only: no function
names, inputs or outputs. Run on the private results folder with the private oracle:
    python gate20/referee/analyze_htq.py <private results dir> <private oracle.py>
O6: HTQ − TQ hidden pass ≥ +3 points (95% CI bootstrapped over functions).
O7: on the functions the handbook documents (oracle.DOCUMENTED), HTQ fixes ≥ 0.9 of N0's edge errors and at least
    0.1 more than TQ."""
import collections, gzip, importlib.util, json, os, random, sys

d, oracle = sys.argv[1], sys.argv[2]
s = importlib.util.spec_from_file_location('o', oracle); o = importlib.util.module_from_spec(s); s.loader.exec_module(o)
def load(a):
    p = os.path.join(d, f'probe_{a}.json')
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
P = {a: load(a) for a in ('N0', 'TQ', 'HTQ')}
def per_function(a):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P[a]: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in x.values()) / len(x) for c, x in t.items()}
pf = {a: per_function(a) for a in P}; cats = sorted(pf['N0']); rnd = random.Random(7)
v = [pf['HTQ'][c] - pf['TQ'][c] for c in cats]
bs = sorted(sum(rnd.choice(v) for _ in v) / len(v) for _ in range(4000))
print(f'O6 HTQ − TQ = {100 * sum(v) / len(v):+.1f} (95% CI {100 * bs[100]:+.1f} to {100 * bs[3899]:+.1f})')
key = lambda r: (r['cat'], r['test'], r['q'])
ok = {a: {key(r): r['ok'] for r in P[a] if r['kind'] == 'edge'} for a in P}
for label, fs in (('documented', set(o.DOCUMENTED)), ('undocumented', set(cats) - set(o.DOCUMENTED))):
    e = [k for k, x in ok['N0'].items() if not x and k[0] in fs]
    if e:
        print(f'O7 {label} functions ({len(fs)}; {len(e)} N0 edge errors): share fixed TQ {sum(ok["TQ"][k] for k in e) / len(e):.2f}, HTQ {sum(ok["HTQ"][k] for k in e) / len(e):.2f}')
