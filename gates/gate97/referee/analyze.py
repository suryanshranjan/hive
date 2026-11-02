"""G97 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate97/referee/analyze.py
Compares Gate 97's five flights (runs/g97_live1-5: the lean reader) with Gates 95-96's ten (runs/g95_live1-5, g96_live1-5: the
same code with the old reader). A flight succeeds if no crash, one branch, >= 24 of 27 hidden.
E1 Hive's own spend, mean per flight: Gate 97 <= 0.3x Gates 95-96
E2 pass^1 >= 0.8              E3 median hidden >= 26
E4 median owner prompts <= 1.2x Gates 95-96's          E5 pass^5 (all five succeed)
Claim: E1, E2 and E3 -> the lean reader stays the default."""
import json, os
from statistics import mean, median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
def load(g): return [json.load(open(os.path.join(ROOT, 'runs', f'g{g}_live{k}', 'flight.json'))) for k in range(1, 6)]
ok = lambda f: f['rc'] == 0 and not f['error'] and len(f['branches']) == 1 and (f['after'].get('passed') or 0) >= 24
B, T = load(95) + load(96), load(97)
for name, R in (('Gates 95-96', B), ('Gate 97', T)):
    print(f"{name}: hidden {[f['after'].get('passed') for f in R]}, prompts {[f['owner_replies'] for f in R]}, Hive's own "
          f"{[f.get('hive_own') for f in R]} (mean ${mean(f['hive_own'] for f in R):.2f}), builders mean ${mean(f['build_cost'] for f in R):.2f}, "
          f"own/builders {mean(f['hive_own'] for f in R) / mean(f['build_cost'] for f in R):.1f}x, pass^1 {sum(ok(f) for f in R)/len(R):.2f}")
by = {}
for f in T:
    for k, v in (f.get('hive_own_by') or {}).items(): by[k] = by.get(k, 0) + v
print('Gate 97 spend by step:', {k: round(v, 2) for k, v in sorted(by.items(), key=lambda x: -x[1])[:8]})
e1 = mean(f['hive_own'] for f in T) <= 0.3 * mean(f['hive_own'] for f in B)
e2 = sum(ok(f) for f in T) >= 4; e3 = median(f['after'].get('passed') or 0 for f in T) >= 26
e4 = median(f['owner_replies'] for f in T) <= 1.2 * median(f['owner_replies'] for f in B); e5 = all(ok(f) for f in T)
print('\npredictions')
for t, x, h in [('E1', "Hive's own spend <= 0.3x", e1), ('E2', 'pass^1 >= 0.8', e2), ('E3', 'median hidden >= 26', e3),
                ('E4', 'median prompts <= 1.2x', e4), ('E5', 'pass^5', e5), ('Claim', 'E1, E2 and E3', e1 and e2 and e3)]:
    print(f'{t} {x} -> {"held" if h else "failed"}')
