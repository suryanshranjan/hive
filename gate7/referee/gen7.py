"""Gate 7 tests. Visible: one test per function holding the owner's two examples. Hidden: 25 tests per function,
3 calls each, each call drawn from EDGE with probability 0.7, else TYPICAL. Expected values from oracle.py.
usage: gen7.py visible|hidden <out_dir> <seed>"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle, cases
def L(v):
    if v is None: return 'NULL'
    if isinstance(v, str): return "'" + v.replace("'", "''") + "'"
    return repr(v)
H = {f: (lambda r, f=f: r.choice(cases.TYPICAL[f])) for f in cases.TYPICAL}
E = {f: (lambda r, f=f: r.choice(cases.EDGE[f])) for f in cases.EDGE}
CATS = sorted(H); AGG = None; LAST_KIND = None
def call(cat, args): return f'{cat.upper()}(' + ', '.join(L(a) for a in args) + ')'
def make(cat, rng, edge_share):
    return [], 'SELECT ' + ', '.join(call(cat, (E[cat] if rng.random() < edge_share else H[cat])(rng)) for _ in range(3))
if __name__ == '__main__':
    kind, out, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    os.makedirs(out, exist_ok=True); n = 0
    for ci, cat in enumerate(CATS):
        if kind == 'visible':
            qs = ['SELECT ' + ', '.join(call(cat, a) for a, _ in cases.VISIBLE[cat])]
        else:
            rng = random.Random(seed + ci * 1000); qs = [make(cat, rng, 0.7)[1] for _ in range(25)]
        for k, q in enumerate(qs):
            rows = [list(r) for r in oracle.connect().execute(q).fetchall()]
            t = dict(id=f'{cat}_{k:03d}', category=cat, setup=[], query=q, expected=rows, ordered=True)
            json.dump(t, open(os.path.join(out, t['id'] + '.json'), 'w')); n += 1
    print(n, kind, 'tests in', out)
