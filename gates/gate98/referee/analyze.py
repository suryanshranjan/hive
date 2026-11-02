"""G98 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate97/referee/analyze.py
Gate 98's five flights (runs/g98_live1-5: the lean reader and the interface check that follows helpers), compared with Gates 95-96 (old reader). A flight succeeds if no crash, one branch, >= 24 of 27 hidden.
F1 Hive's own spend, mean per flight, <= 1.5x the builders' mean
F2 pass^5 (all five succeed)        F3 median hidden >= 26        F4 median owner prompts <= 35"""
import json, os
from statistics import mean, median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
def load(g): return [json.load(open(os.path.join(ROOT, 'runs', f'g{g}_live{k}', 'flight.json'))) for k in range(1, 6)]
ok = lambda f: f['rc'] == 0 and not f['error'] and len(f['branches']) == 1 and (f['after'].get('passed') or 0) >= 24
B, T = load(95) + load(96), load(98)
for name, R in (('Gates 95-96', B), ('Gate 98', T)):
    print(f"{name}: hidden {[f['after'].get('passed') for f in R]}, prompts {[f['owner_replies'] for f in R]}, Hive's own "
          f"{[f.get('hive_own') for f in R]} (mean ${mean(f['hive_own'] for f in R):.2f}), builders mean ${mean(f['build_cost'] for f in R):.2f}, "
          f"own/builders {mean(f['hive_own'] for f in R) / mean(f['build_cost'] for f in R):.1f}x, pass^1 {sum(ok(f) for f in R)/len(R):.2f}")
by = {}
for f in T:
    for k, v in (f.get('hive_own_by') or {}).items(): by[k] = by.get(k, 0) + v
print('Gate 98 spend by step:', {k: round(v, 2) for k, v in sorted(by.items(), key=lambda x: -x[1])[:8]})
f1 = mean(f['hive_own'] for f in T) <= 1.5 * mean(f['build_cost'] for f in T); f2 = all(ok(f) for f in T)
f3 = median(f['after'].get('passed') or 0 for f in T) >= 26; f4 = median(f['owner_replies'] for f in T) <= 35
print('\npredictions')
for t, x, h in [('F1', "Hive's own <= 1.5x builders'", f1), ('F2', 'pass^5', f2), ('F3', 'median hidden >= 26', f3), ('F4', 'median prompts <= 35', f4)]:
    print(f'{t} {x} -> {"held" if h else "failed"}')
