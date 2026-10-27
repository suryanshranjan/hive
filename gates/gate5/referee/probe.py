"""Score a swarm's engine call by call against the private intent.
Regenerates the hidden suite's calls (same seed as gen3 hidden) and records, for every single call,
whether it was drawn as a happy-path or an edge case, the oracle's answer and the engine's answer.
usage: python3 probe.py <engine_dir> <out.json> [seed=900000]"""
import json, os, random, signal, sys
here = os.path.dirname(os.path.abspath(__file__))
engine_dir, out = os.path.abspath(sys.argv[1]), sys.argv[2]
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 5200000
sys.path.insert(0, here)
import gen5 as gen3, oracle
sys.path.insert(0, engine_dir)
import minisql

def norm(v):
    if isinstance(v, bool): v = int(v)
    if isinstance(v, (int, float)): return ('n', round(float(v), 6))
    if v is None: return ('0',)
    return ('s', str(v))

class TO(Exception): pass
def _alarm(*a): raise TO()
signal.signal(signal.SIGALRM, _alarm)

def run(setup, q):
    signal.alarm(3)
    try:
        con = minisql.connect()
        for s in setup: con.execute(s)
        return [list(r) for r in con.execute(q)], None
    except BaseException as e:
        return None, f'{type(e).__name__}: {e}'[:120]
    finally:
        signal.alarm(0)

def oracle_run(setup, q):
    con = oracle.connect()
    for s in setup: con.execute(s)
    return [list(r) for r in con.execute(q).fetchall()]

rows = []
for ci, cat in enumerate(gen3.CATS):
    rng = random.Random(seed + ci * 1000)
    for k in range(25):
        if cat == gen3.AGG:
            setup, q = gen3.make(cat, rng, 0.7)
            calls = [(setup, q, gen3.LAST_KIND)]
        else:
            calls = []
            for _ in range(3):
                edge = rng.random() < 0.7
                args = (gen3.E[cat] if edge else gen3.H[cat])(rng)
                calls.append(([], 'SELECT ' + gen3.call(cat, args), 'edge' if edge else 'happy'))
        for setup, q, kind in calls:
            exp = oracle_run(setup, q)
            got, err = run(setup, q)
            ok = got is not None and [[norm(v) for v in r] for r in got] == [[norm(v) for v in r] for r in exp]
            rows.append(dict(cat=cat, test=f'{cat}_{k:03d}', kind=kind, q=q, expected=exp, got=got, err=err, ok=ok))
json.dump(rows, open(out, 'w'), default=str)
print(len(rows), 'calls', sum(r['ok'] for r in rows), 'correct')
