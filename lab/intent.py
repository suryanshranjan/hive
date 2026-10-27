#!/usr/bin/env python3
"""Intent tests from a rule-giver's oracle module (the Gate 5/6 contract), and call-by-call scoring.

The oracle module must define: SPEC, SCALARS {name: (fn, nargs)}, TYPICAL {name: [args...]},
EDGE {name: [args...]}, connect(); and optionally AGGREGATE (name, class), AGG_TYPICAL, AGG_EDGE.

usage:
  intent.py tests  <oracle.py> visible <out_dir> <seed>     # 2 tests per function, typical calls only
  intent.py tests  <oracle.py> hidden  <out_dir> <seed>     # 25 tests per function, 70% edge calls
  intent.py probe  <oracle.py> <engine_dir> <out.json> <hidden seed>   # score an engine call by call

Generation reproduces Gates 5 and 6 exactly (same random scheme), so their published seeds regenerate their suites."""
import importlib.util, json, os, random, signal, sys

def load_oracle(path):
    path = os.path.abspath(path)
    # never let a project's sqlite3 stub shadow the real module
    sys.path[:] = [p for p in sys.path if p not in ('', os.getcwd())]
    spec = importlib.util.spec_from_file_location('hive_oracle', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def L(v):
    if v is None: return 'NULL'
    if isinstance(v, str): return "'" + v.replace("'", "''") + "'"
    return repr(v)

class Gen:
    def __init__(self, o):
        self.o = o
        self.AGG = o.AGGREGATE[0] if getattr(o, 'AGGREGATE', None) else None
        self.CATS = sorted(o.SCALARS) + ([self.AGG] if self.AGG else [])
    def call(self, cat, args):
        return f'{cat.upper()}(' + ', '.join(L(a) for a in args) + ')'
    def make(self, cat, rng, edge_share):
        """returns (setup, [(query, kind)]) where a scalar test has 3 calls and an aggregate test has 1"""
        if cat == self.AGG:
            edge = rng.random() < edge_share
            vals = rng.choice(self.o.AGG_EDGE if edge else self.o.AGG_TYPICAL)
            setup = ['CREATE TABLE m (id INTEGER, v)']
            if vals:
                setup.append('INSERT INTO m VALUES ' + ', '.join(f'({i}, {L(v)})' for i, v in enumerate(vals, 1)))
            return setup, [(f'SELECT {self.AGG.upper()}(v) FROM m', 'edge' if edge else 'happy')]
        calls = []
        for _ in range(3):
            edge = rng.random() < edge_share
            args = rng.choice(self.o.EDGE[cat] if edge else self.o.TYPICAL[cat])
            calls.append((self.call(cat, args), 'edge' if edge else 'happy'))
        return [], calls
    def tests(self, kind, seed):
        per, edge = (2, 0.0) if kind == 'visible' else (25, 0.7)
        for ci, cat in enumerate(self.CATS):
            rng = random.Random(seed + ci * 1000)
            for k in range(per):
                setup, calls = self.make(cat, rng, edge)
                q = calls[0][0] if cat == self.AGG else 'SELECT ' + ', '.join(c for c, _ in calls)
                yield cat, k, setup, q, calls

def oracle_rows(o, setup, q):
    con = o.connect()
    for s in setup: con.execute(s)
    return [list(r) for r in con.execute(q).fetchall()]

def norm(v):
    if isinstance(v, bool): v = int(v)
    if isinstance(v, (int, float)): return ('n', round(float(v), 6))
    if v is None: return ('0',)
    if isinstance(v, (bytes, bytearray)): return ('s', bytes(v).hex())
    return ('s', str(v))

def cmd_tests(oracle_path, kind, out, seed):
    o = load_oracle(oracle_path); g = Gen(o); os.makedirs(out, exist_ok=True); n = 0
    for cat, k, setup, q, _ in g.tests(kind, seed):
        t = dict(id=f'{cat}_{k:03d}', category=cat, setup=setup, query=q, expected=oracle_rows(o, setup, q), ordered=True)
        json.dump(t, open(os.path.join(out, t['id'] + '.json'), 'w')); n += 1
    print(n, kind, 'tests in', out)

class _TO(Exception): pass
def _alarm(*a): raise _TO()

def cmd_probe(oracle_path, engine_dir, out, seed):
    o = load_oracle(oracle_path); g = Gen(o)
    sys.path.insert(0, os.path.abspath(engine_dir)); import minisql
    signal.signal(signal.SIGALRM, _alarm); rows = []
    for cat, k, setup, _, calls in g.tests('hidden', seed):
        for q, kind in calls:
            if cat != g.AGG: q = 'SELECT ' + q
            exp = oracle_rows(o, setup, q)
            signal.alarm(3)
            try:
                con = minisql.connect()
                for s in setup: con.execute(s)
                got, err = [list(r) for r in con.execute(q)], None
            except BaseException as e:
                got, err = None, f'{type(e).__name__}: {e}'[:120]
            finally:
                signal.alarm(0)
            ok = got is not None and [[norm(v) for v in r] for r in got] == [[norm(v) for v in r] for r in exp]
            rows.append(dict(cat=cat, test=f'{cat}_{k:03d}', kind=kind, q=q, expected=exp, got=got, err=err, ok=ok))
    json.dump(rows, open(out, 'w'), default=str)
    tests = {}
    for r in rows: tests.setdefault(r['test'], []).append(r['ok'])
    edge = [r['ok'] for r in rows if r['kind'] == 'edge']
    print(f"{len(rows)} calls, {sum(r['ok'] for r in rows)} correct; hidden tests {sum(all(v) for v in tests.values())}/{len(tests)}; "
          f"edge calls {sum(edge)}/{len(edge)}")

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 5 and a[0] == 'tests': cmd_tests(a[1], a[2], a[3], int(a[4]))
    elif len(a) == 5 and a[0] == 'probe': cmd_probe(a[1], a[2], a[3], int(a[4]))
    else: print(__doc__); sys.exit(2)
