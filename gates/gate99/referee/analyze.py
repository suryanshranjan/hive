"""G99 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate99/referee/analyze.py
Five overnight flights (runs/g99_overnight1-5). A flight succeeds if no crash, one branch, >= 24 of 27 hidden after the morning.
Earlier overnight flights after the morning (Gates 76, 77 control, 81, 82, 83): 22, 26, 24, 25, 25, 25, 25.
N1 pass^1 >= 0.8          N2 median hidden after the morning >= 25
N3 median morning prompts <= 20          N4 total cost (builders + Hive's own) per flight <= $1.50"""
import json, os
from statistics import median, mean
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
R = [json.load(open(os.path.join(ROOT, 'runs', f'g99_overnight{k}', 'flight.json'))) for k in range(1, 6)]
ok = lambda f: f['rc'] == 0 and not f['error'] and len(f['branches']) == 1 and (f['after'].get('passed') or 0) >= 24
for k, f in enumerate(R, 1):
    print(f"overnight{k}: night {f.get('night', {}).get('passed')}, after the morning {f['after'].get('passed')}/27, prompts {f['owner_replies']}, "
          f"{f['minutes']} min, builders ${f['build_cost']}, Hive's own ${f.get('hive_own')}, success {ok(f)}")
p1 = sum(ok(f) for f in R) / 5; mh = median(f['after'].get('passed') or 0 for f in R); mp = median(f['owner_replies'] for f in R)
cost = mean(f['build_cost'] + (f.get('hive_own') or 0) for f in R)
print(f"\npass^1 {p1:.2f}, pass^5 {all(ok(f) for f in R)}, median after {mh}, median prompts {mp}, mean cost ${cost:.2f}")
print('\npredictions')
for t, x, h in [('N1', 'pass^1 >= 0.8', p1 >= 0.8), ('N2', 'median after the morning >= 25', mh >= 25),
                ('N3', 'median morning prompts <= 20', mp <= 20), ('N4', 'mean cost <= $1.50', cost <= 1.5)]:
    print(f'{t} {x} -> {"held" if h else "failed"}')
