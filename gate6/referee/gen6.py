"""Tests for Gate 6's 20 business functions, built from the independent rule-giver's own lists in oracle.py.
Visible: 2 tests per function from TYPICAL (3 calls each) or AGG_TYPICAL. Hidden: 25 per function, each call drawn
from EDGE with probability 0.7, else TYPICAL (the aggregate: one input list per test, same probabilities).
usage: gen5.py visible|hidden <out_dir> <seed>"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle

def L(v):
    if v is None: return 'NULL'
    if isinstance(v, str): return "'" + v.replace("'", "''") + "'"
    return repr(v)

H = {f: (lambda r, f=f: r.choice(oracle.TYPICAL[f])) for f in oracle.SCALARS}
E = {f: (lambda r, f=f: r.choice(oracle.EDGE[f])) for f in oracle.SCALARS}
AGG = oracle.AGGREGATE[0]
CATS = sorted(H) + [AGG]
LAST_KIND = None

def call(cat, args):
    return f'{cat.upper()}(' + ', '.join(L(a) for a in args) + ')'

def make(cat, rng, edge_share):
    global LAST_KIND
    if cat == AGG:
        edge = rng.random() < edge_share
        vals = rng.choice(oracle.AGG_EDGE if edge else oracle.AGG_TYPICAL)
        LAST_KIND = 'edge' if edge else 'happy'
        setup = ['CREATE TABLE m (id INTEGER, v)']
        if vals:
            setup.append('INSERT INTO m VALUES ' + ', '.join(f'({i}, {L(v)})' for i, v in enumerate(vals, 1)))
        return setup, f'SELECT {AGG.upper()}(v) FROM m'
    calls = []
    for _ in range(3):
        args = (E[cat] if rng.random() < edge_share else H[cat])(rng)
        calls.append(call(cat, args))
    return [], 'SELECT ' + ', '.join(calls)

if __name__ == '__main__':
    kind, out, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    per, edge = (2, 0.0) if kind == 'visible' else (25, 0.7)
    os.makedirs(out, exist_ok=True)
    n = 0
    for ci, cat in enumerate(CATS):
        rng = random.Random(seed + ci * 1000)
        for k in range(per):
            setup, q = make(cat, rng, edge)
            con = oracle.connect()
            for s in setup: con.execute(s)
            rows = [list(r) for r in con.execute(q).fetchall()]
            t = dict(id=f'{cat}_{k:03d}', category=cat, setup=setup, query=q, expected=rows, ordered=True)
            json.dump(t, open(os.path.join(out, t['id'] + '.json'), 'w')); n += 1
    print(n, kind, 'tests in', out)
