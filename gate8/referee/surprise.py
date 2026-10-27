"""Surprise test: replay every answered question against the no-question team's final engine.
A 'surprise' is an answered value that differs from what that engine returns (what builders would have guessed).
    python3 surprise.py <N0 engine dir> <asks log> <allowance json> <probe_N0.json.gz> <probe_NQ.json.gz>
Prints, per function: allowance, questions, surprises, and the share of N0's edge errors that NQ fixed."""
import gzip, json, sys

eng, asks, allow, p0, p1 = sys.argv[1:6]
sys.path.insert(0, eng)
import minisql

al = json.load(open(allow))
al = al.get('allow', al)

def same(a, g):
    if isinstance(a, (int, float)) and isinstance(g, (int, float)) and not isinstance(a, bool):
        return abs(a - g) < 1e-9
    return a == g

surp, nq = {}, {}
for line in open(asks):
    r = json.loads(line)
    ans = r['resp'].get('answer')
    if not r.get('charged') or ans is None:
        continue
    f = [k for k in al if k.upper() + '(' in r['sql'].upper()][0]
    try:
        got = list(list(minisql.connect().execute(r['sql']))[0])
    except Exception:
        got = [object()] * len(ans)
    surp[f] = surp.get(f, 0) + sum(not same(a, g) for a, g in zip(ans, got))
    nq[f] = nq.get(f, 0) + 1

def edge(path):
    d = {}
    for r in json.load(gzip.open(path)):
        if r['kind'] == 'edge':
            d.setdefault(r['cat'], []).append(r['ok'])
    return d

e0, e1 = edge(p0), edge(p1)
rows = []
for f in sorted(al, key=lambda f: (al[f], f)):
    err0 = len(e0[f]) - sum(e0[f])
    fixed = (sum(e1[f]) - sum(e0[f])) / err0 if err0 else None
    rows.append(dict(f=f, allow=al[f], questions=nq.get(f, 0), surprises=surp.get(f, 0), errors0=err0, fixed=fixed))
    print(f"{al[f]} {f:24s} questions {nq.get(f, 0)}  surprises {surp.get(f, 0)}  N0 edge errors {err0:3d}  "
          f"share fixed {'n/a' if fixed is None else f'{fixed:+.2f}'}")
print(json.dumps(rows))
