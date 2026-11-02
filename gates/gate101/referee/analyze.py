"""G101 registered analysis (committed with the predictions, before any flight):
    python3 gates/gate92/referee/analyze.py
Day 2 hidden tests (private/g92/test_day2.py, 29 cases from the owner's changed policy; 12 of them differ from day 1's rules).
D1 arm F (no memory of day 1): median >= 26 of 29
D2 arm M (memory of day 1's rulings kept): median <= F's median - 5 (the old rulings win over his new word)
D3 arm M asks the owner fewer prompts than F (median)
Also: day 1's score and how many rulings Hive kept."""
import json, os
from statistics import median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
d1 = json.load(open(os.path.join(ROOT, 'runs', 'g101_day1', 'flight.json')))
print(f"day 1: hidden {d1['after'].get('line')}, prompts {d1['owner_replies']}, rulings kept {d1.get('rulings_kept')}")
R = {a: [json.load(open(os.path.join(ROOT, 'runs', f'g101_day2_{a}{k}', 'flight.json'))) for k in (1, 2, 3)] for a in 'MF'}
for a, rs in R.items():
    print(f"day 2 {a}: hidden {[r['after'].get('passed') for r in rs]} of 29, prompts {[r['owner_replies'] for r in rs]}, minutes {[r['minutes'] for r in rs]}")
m = {a: median(r['after'].get('passed') or 0 for r in rs) for a, rs in R.items()}
p = {a: median(r['owner_replies'] for r in rs) for a, rs in R.items()}
print('\npredictions')
for t, x, ok in [('D1', f"F median >= 26 ({m['F']})", m['F'] >= 26), ('D2', f"M median <= F - 5 ({m['M']} vs {m['F']})", m['M'] <= m['F'] - 5),
                 ('D3', f"M prompts < F ({p['M']} vs {p['F']})", p['M'] < p['F'])]:
    print(f'{t} {x} -> {"held" if ok else "failed"}')
