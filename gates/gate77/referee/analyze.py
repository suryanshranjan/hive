"""G77 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate77/referee/analyze.py runs/g77_control1 runs/g77_control2 runs/g77_control3 runs/g77_split1 runs/g77_split2 runs/g77_split3
Per flight: hidden tests passed at night and after the morning (of 27), questions recorded overnight (the owner's morning
load), who recorded them, whether the split engaged, builders' cost.
N1 split's mean after the morning >= control's mean + 2 (of 27)
N2 in every split flight the split engaged and every recorded question came from the business builder
N3 split's mean questions recorded <= 1.5x control's
N4 no crash in any of the six flights, and the morning fix ran in each
Claim: N1 and N3 -> the overnight split ships as the default."""
import glob, json, os, sys
from statistics import mean
def one(d):
    f = json.load(open(os.path.join(d, 'flight.json')))
    b = sorted(glob.glob(os.path.join(d, 'hive_state', 'runs', '*', 'build')))
    b = b[-1] if b else None
    ps = sorted(glob.glob(os.path.join(b, 'prompts', '*.md'))) if b else []
    biz = bool(ps) and 'Your role: the business builder' in open(ps[-1]).read()
    rest = len(ps) > 1 and all('Your role: build the rest' in open(p).read() for p in ps[:-1])
    qs = [json.load(open(q)) for q in glob.glob(os.path.join(b, 'owner', 'questions', '*.json'))] if b else []
    askers = sorted({q.get('worker') for q in qs if q.get('worker')})
    fixed = bool(b) and os.path.isdir(os.path.join(os.path.dirname(b), 'fix'))
    return dict(arm=f.get('arm'), k=f.get('k'), rc=f['rc'], error=bool(f['error']), minutes=f['minutes'],
                night=f.get('night', {}).get('passed', 0), after=f['after'].get('passed', 0), questions=len(qs),
                askers=askers, builders=len(ps), split=biz and rest, last=os.path.basename(ps[-1])[:-3] if ps else None,
                fixed=fixed, build_cost=f['build_cost'], owner_cost=f['owner_cost'])
R = [one(d) for d in sys.argv[1:]]
for r in R:
    print(r)
C = [r for r in R if r['arm'] == 'control']; S = [r for r in R if r['arm'] == 'split']
m = lambda rs, k: mean(r[k] for r in rs) if rs else float('nan')
print(f"\ncontrol: night {m(C,'night'):.1f}, after {m(C,'after'):.2f}/27, questions {m(C,'questions'):.1f}, {m(C,'minutes'):.1f} min, builders ${m(C,'build_cost'):.2f}")
print(f"split:   night {m(S,'night'):.1f}, after {m(S,'after'):.2f}/27, questions {m(S,'questions'):.1f}, {m(S,'minutes'):.1f} min, builders ${m(S,'build_cost'):.2f}")
n1 = m(S, 'after') >= m(C, 'after') + 2
n2 = all(r['split'] and r['askers'] in ([], [r['last']]) for r in S)
n3 = m(S, 'questions') <= 1.5 * m(C, 'questions')
n4 = all(r['rc'] == 0 and not r['error'] and r['fixed'] for r in R) and len(R) == 6
print('\npredictions')
for tag, text, held in [('N1', f"split after {m(S,'after'):.2f} >= control {m(C,'after'):.2f} + 2", n1),
                        ('N2', 'split engaged, only the business builder recorded', n2),
                        ('N3', f"split questions {m(S,'questions'):.1f} <= 1.5 x control {m(C,'questions'):.1f}", n3),
                        ('N4', 'no crash, morning fix ran, six flights', n4),
                        ('Claim', 'N1 and N3', n1 and n3)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
