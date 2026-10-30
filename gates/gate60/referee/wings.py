#!/usr/bin/env python3
"""Gate 60 harness: run one build (or, for scoring only, the oracle) on a list of calls and record what comes out.

usage: wings.py run <engine dir | oracle.py> <calls.json> <aggregate name> <out.json>

calls.json: [{"function": f, "args": [...]}] for a scalar function, [{"function": agg, "values": [...]}] for the
aggregate (the column's values over one group of rows). Each call gets 3 seconds. The output keeps, per call, the
normalized value (intent.norm) or the error, so two builds can be compared call by call."""
import json, os, signal, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'lab'))
import intent

class _TO(Exception): pass
def _alarm(*a): raise _TO()

def query(c, agg):
    """(setup, query) for one call, or None if it cannot be written as SQL."""
    def ok(v):
        return v is None or isinstance(v, (str, int, float)) and not isinstance(v, bool)
    f = str(c.get('function', ''))
    if not f.replace('_', '').isalnum():
        return None
    if f == agg:
        vals = [int(v) if isinstance(v, bool) else v for v in (c.get('values') or [])]
        if not all(ok(v) for v in vals):
            return None
        setup = ['CREATE TABLE m (id INTEGER, v)']
        if vals:
            setup.append('INSERT INTO m VALUES ' + ', '.join(f'({i}, {intent.L(v)})' for i, v in enumerate(vals, 1)))
        return setup, f'SELECT {f.upper()}(v) FROM m'
    args = [int(v) if isinstance(v, bool) else v for v in (c.get('args') or [])]
    if not all(ok(v) for v in args):
        return None
    return [], f'SELECT {f.upper()}(' + ', '.join(intent.L(a) for a in args) + ')'

def run(target, calls, agg):
    if target.endswith('.py'):
        o = intent.load_oracle(target); connect = o.connect
    else:
        sys.path.insert(0, os.path.abspath(target)); import minisql; connect = minisql.connect
    signal.signal(signal.SIGALRM, _alarm); out = []
    for c in calls:
        q = query(c, agg)
        if q is None:
            out.append(None); continue
        setup, sql = q
        signal.alarm(3)
        try:
            con = connect()
            for s in setup: con.execute(s)
            rows = [list(r) for r in con.execute(sql)]
            v = rows[0][0] if rows and rows[0] else None
            out.append(dict(sql=sql, value=list(intent.norm(v)), shown=v if isinstance(v, (int, float, str)) or v is None else str(v)))
        except BaseException as e:
            out.append(dict(sql=sql, error=f'{type(e).__name__}: {e}'[:160]))
        finally:
            signal.alarm(0)
    return out

def same(a, b):
    """Two results agree: the same value, or both an error."""
    if a is None or b is None:
        return True
    if 'error' in a or 'error' in b:
        return 'error' in a and 'error' in b
    return a['value'] == b['value']

def label(c, agg):
    """The call as a reader sees it: late_fee(10000, 31), or avg_rating over the rows [4, 5, null]."""
    if c['function'] == agg:
        return f"{c['function']} over the rows {json.dumps(c.get('values') or [])}"
    return f"{c['function']}(" + ', '.join(json.dumps(a) for a in c.get('args') or []) + ')'

def shown(r):
    return f"error ({r['error'].split(':')[0]})" if 'error' in r else json.dumps(r['shown'])

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 5 and a[0] == 'run':
        json.dump(run(a[1], json.load(open(a[2])), a[3]), open(a[4], 'w'), default=str)
    else:
        print(__doc__); sys.exit(2)
