"""Scores Gate 103b's registered predictions. X3 is measured as: the check's own spend (hive_own_by['examples.check'])
plus the cost of any examples fix round (state.json, examples_fix* phases), mean per flight; and median flight minutes
against the comparison flights (Gate 101 F for the drift arm, Gate 98 for live)."""
import csv, glob, json, os, statistics as st
def load(pat):
    out = []
    for f in sorted(glob.glob(pat)):
        d = json.load(open(f)); run = os.path.dirname(f)
        s = (glob.glob(f'{run}/hive_state/runs/*/state.json') or [None])[0]
        s = json.load(open(s)) if s else {}
        ex = s.get('examples') or []
        d['_check'] = (d.get('hive_own_by') or {}).get('examples.check', 0) or 0
        d['_flags'] = [len((e or {}).get('failing') or []) for e in ex]
        fx = glob.glob(f'{run}/hive_state/runs/*/examples_fix*')
        d['_fixes'] = len(fx)
        d['_fixcost'] = sum(float(r['cost_usd'] or 0) for p in fx if os.path.exists(f'{p}/agents.csv') for r in csv.DictReader(open(f'{p}/agents.csv')))
        out.append(d)
    return out
F = load('runs/g103_day2_F*/flight.json'); L = load('runs/g103_live*/flight.json')
F0 = load('gates/gate101/results/day2_F*/flight.json'); L0 = load('gates/gate98/results/live*/flight.json')
h = lambda d: (d.get('after') or {}).get('passed', 0)
for name, xs in (('drift F + check', F), ('live + check', L)):
    for d in xs:
        print(f"{name:16} hidden {h(d)}  prompts {d['owner_replies']}  minutes {d['minutes']}  check ${d['_check']:.2f}  flags {d['_flags']}  fix rounds {d['_fixes']} (${d['_fixcost']:.2f})  build ${d['build_cost']}  own ${d['hive_own']}")
mF = st.median([h(d) for d in F]) if F else 0
print(f"\nX1 F-with-check median hidden >= 26 of 29 ({mF}; Gate 101 F: {st.median([h(d) for d in F0])}) ->", 'held' if mF >= 26 else 'failed')
print('X2 live flights all >= 24 of 27', [h(d) for d in L], '->', 'held' if L and all(h(d) >= 24 for d in L) else 'failed')
add = st.mean([d['_check'] + d['_fixcost'] for d in F + L]) if F + L else 0
dm = max((st.median([d['minutes'] for d in F]) - st.median([d['minutes'] for d in F0])) if F else 0,
         (st.median([d['minutes'] for d in L]) - st.median([d['minutes'] for d in L0])) if L else 0)
print(f"X3 the check and its fix rounds ${add:.2f} a flight, minutes +{dm:.1f} -> " +
      ('held' if add <= 0.60 and dm <= 4 else 'failed'))
