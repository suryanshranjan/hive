"""G90 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate87/referee/analyze.py
Compares Gate 90's five flights (runs/g90_live1-5: after the placeholder fix) with Gate 85's (runs/g85_live1-5). A flight succeeds if no crash, one branch, >= 24 of 27 hidden.
J1 no delivered build has a placeholder left in shop/*.py (all five)
J2 pass^1 >= 0.8
J3 median hidden >= 26
J4 median owner prompts <= 1.2x Gate 85's
Claim: J1, J2 and J3 -> the fix ships."""
import json, os
from statistics import mean, median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
def load(g): return [json.load(open(os.path.join(ROOT, 'runs', f'g{g}_live{k}', 'flight.json'))) for k in range(1, 6)]
ok = lambda f: f['rc'] == 0 and not f['error'] and len(f['branches']) == 1 and (f['after'].get('passed') or 0) >= 24
B, T = load(85), load(90)
for name, R in (('Gate 85', B), ('Gate 90', T)):
    print(f"{name}: hidden {[f['after'].get('passed') for f in R]}, prompts {[f['owner_replies'] for f in R]}, "
          f"Hive's own {[f.get('hive_own') for f in R]} (mean ${mean(f.get('hive_own') or 0 for f in R):.2f}), builders mean ${mean(f['build_cost'] for f in R):.2f}, "
          f"pass^1 {sum(ok(f) for f in R)/5:.2f}, minutes {[f['minutes'] for f in R]}")
import glob, re
def placeholders(k):
    return [f for f in glob.glob(os.path.join(ROOT, 'runs', f'g90_live{k}', 'delivered', 'shop', '*.py')) if re.search('placeholder', open(f).read(), re.I)]
left = {k: placeholders(k) for k in range(1, 6)}
print('placeholders left:', {k: [os.path.basename(f) for f in v] for k, v in left.items()})
j1 = not any(left.values()); j2 = sum(ok(f) for f in T) >= 4; j3 = median(f['after'].get('passed') or 0 for f in T) >= 26
j4 = median(f['owner_replies'] for f in T) <= 1.2 * median(f['owner_replies'] for f in B)
print('\npredictions')
for tag, text, held in [('J1', 'no placeholder left in any delivery', j1), ('J2', 'pass^1 >= 0.8', j2), ('J3', 'median hidden >= 26', j3),
                        ('J4', "median prompts <= 1.2x Gate 85's", j4), ('Claim', 'J1, J2 and J3', j1 and j2 and j3)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
