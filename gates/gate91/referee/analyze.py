"""G91 registered analysis (committed with the predictions, before the flights):
    python3 gates/gate87/referee/analyze.py
Compares Gate 91's five flights (runs/g91_live1-5: Hive's own reading steps on Claude Haiku 5.5) with Gate 90's (runs/g90_live1-5,
the same flow on the CLI's default model). A flight succeeds if no crash, one branch, >= 24 of 27 hidden.
H1 Hive's own spend, mean over flights: Gate 91 <= 0.4x Gate 90
H2 pass^1 does not drop: Gate 91 >= 0.8 (at least 4 of 5)
H3 median hidden: Gate 91 >= 26
H4 median owner prompts: Gate 91 <= 1.2x Gate 90 (the cheaper reader does not make the owner repeat himself)
Claim: H1, H2 and H3 -> Hive's own reading steps run on the small model by default."""
import json, os
from statistics import mean, median
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
def load(g): return [json.load(open(os.path.join(ROOT, 'runs', f'g{g}_live{k}', 'flight.json'))) for k in range(1, 6)]
ok = lambda f: f['rc'] == 0 and not f['error'] and len(f['branches']) == 1 and (f['after'].get('passed') or 0) >= 24
B, T = load(90), load(91)
for name, R in (('Gate 90', B), ('Gate 91', T)):
    print(f"{name}: hidden {[f['after'].get('passed') for f in R]}, prompts {[f['owner_replies'] for f in R]}, "
          f"Hive's own {[f.get('hive_own') for f in R]} (mean ${mean(f.get('hive_own') or 0 for f in R):.2f}), builders mean ${mean(f['build_cost'] for f in R):.2f}, "
          f"pass^1 {sum(ok(f) for f in R)/5:.2f}, minutes {[f['minutes'] for f in R]}")
h1 = mean(f['hive_own'] for f in T) <= 0.4 * mean(f['hive_own'] for f in B)
h2 = sum(ok(f) for f in T) >= 4; h3 = median(f['after'].get('passed') or 0 for f in T) >= 26
h4 = median(f['owner_replies'] for f in T) <= 1.2 * median(f['owner_replies'] for f in B)
print('\npredictions')
for tag, text, held in [('H1', "Hive's own spend <= 0.4x Gate 90's", h1), ('H2', 'pass^1 >= 0.8', h2), ('H3', 'median hidden >= 26', h3),
                        ('H4', "median prompts <= 1.2x Gate 90's", h4), ('Claim', 'H1, H2 and H3', h1 and h2 and h3)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
