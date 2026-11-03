"""Scores Gate 104's registered predictions (committed with them, before any flight). From the repo root:
    python3 gates/gate104/referee/analyze104.py
Reads runs/g104_P*/flight.json and runs/g104_B*/flight.json. Hidden = the delivered branch's hidden tests passed (of 27)."""
import glob, json, statistics as st

load = lambda pat: [json.load(open(f)) for f in sorted(glob.glob(pat))]
P, B = load('runs/g104_P*/flight.json'), load('runs/g104_B*/flight.json')
h = lambda d: (d.get('after') or {}).get('passed', 0)
for name, xs in (('P (each answer confirmed)', P), ('B (confirmed once, at the end)', B)):
    for d in xs:
        print(f"{name:32} hidden {h(d):2d}/27  prompts {d['owner_replies']:3d}  read-back confirmations {d.get('confirmations', 0):2d}  "
              f"minutes {d['minutes']}  build ${d['build_cost']}  own ${d['hive_own']}  owner words {d.get('owner_typed_words')}")
med = lambda xs, f: st.median([f(d) for d in xs]) if xs else 0
pP, pB = med(P, lambda d: d['owner_replies']), med(B, lambda d: d['owner_replies'])
hP, hB = med(P, h), med(B, h)
print(f'\nmedian prompts P {pP} vs B {pB}; median hidden P {hP} vs B {hB}')
q1 = bool(P and B) and pB <= pP - 5
q2 = bool(B) and all(h(d) >= 24 for d in B)
q3 = bool(P and B) and hB >= hP - 1
print('Q1 B saves >= 5 prompts (median):', pP - pB, '->', 'held' if q1 else 'failed')
print('Q2 every B flight >= 24 of 27:', [h(d) for d in B], '->', 'held' if q2 else 'failed')
print('Q3 B median hidden >= P median - 1:', hB, 'vs', hP, '->', 'held' if q3 else 'failed')
print('Ship (B becomes the default):', 'FIRED' if q1 and q2 and q3 else 'did not fire')
kill = (bool(B) and any(h(d) < 24 for d in B) and all(h(d) >= 24 for d in P)) or (bool(P and B) and hB < hP - 1)
print('Kill (each answer stays confirmed):', 'FIRED' if kill else 'did not fire')
