"""G80 registered analysis (committed with the predictions, before any run):
    python3 gates/gate80/referee/analyze.py runs/g80_F1 runs/g80_A1 runs/g80_A2 runs/g80_F2 runs/g80_F3 runs/g80_A3
Duplicated: of the 12 emptied functions, how many were rebuilt in the own commits (landed or not) of 2 or more builders
(dup.py; Gate 78's runs measured this way: 7, 6, 1, 6).
D1 A's mean duplicated <= half of F's, and F's mean >= 2      D2 A cost <= 0.85x F
D3 A hidden >= F - 3 (of 61)                                   D4 A wall <= 1.1x F (prepare included)
Claim: D1 and D2 and D3."""
import json, os, sys
from statistics import mean
R = [json.load(open(os.path.join(d, 'result.json'))) for d in sys.argv[1:]]
for r in R:
    print(f"{r['arm']}{r['k']}: hidden {r['hidden_passed']}/{r['hidden_total']}, duplicated {r['duplicated']} of 12, "
          f"wall {r['wall_minutes']} min (+{r['prep_seconds']} s prepare), cost ${r['cost']}, tokens {r['tokens']:,}, "
          f"areas {len(r['areas'] or {})}, locks {len(r['locks'])}")
F = [r for r in R if r['arm'] == 'F']; A = [r for r in R if r['arm'] == 'A']
m = lambda rs, f: mean(f(r) for r in rs)
d = (m(F, lambda r: r['duplicated']), m(A, lambda r: r['duplicated'])); c = (m(F, lambda r: r['cost']), m(A, lambda r: r['cost']))
h = (m(F, lambda r: r['hidden_passed']), m(A, lambda r: r['hidden_passed']))
w = (m(F, lambda r: r['wall_minutes'] + r['prep_seconds'] / 60), m(A, lambda r: r['wall_minutes'] + r['prep_seconds'] / 60))
print(f"\nF: duplicated {d[0]:.2f}, cost ${c[0]:.2f}, hidden {h[0]:.2f}, wall {w[0]:.1f} min")
print(f"A: duplicated {d[1]:.2f}, cost ${c[1]:.2f}, hidden {h[1]:.2f}, wall {w[1]:.1f} min")
d1 = d[0] >= 2 and d[1] <= d[0] / 2; d2 = c[1] <= 0.85 * c[0]; d3 = h[1] >= h[0] - 3; d4 = w[1] <= 1.1 * w[0]
print('\npredictions')
for tag, text, ok in [('D1', f"A duplicated {d[1]:.2f} <= half of F {d[0]:.2f} (F >= 2)", d1),
                      ('D2', f"A cost {c[1]:.2f} <= 0.85 x F {c[0]:.2f} (ratio {c[1]/c[0]:.2f})", d2),
                      ('D3', f"A hidden {h[1]:.2f} >= F {h[0]:.2f} - 3", d3),
                      ('D4', f"A wall {w[1]:.1f} <= 1.1 x F {w[0]:.1f}", d4),
                      ('Claim', 'D1 and D2 and D3', d1 and d2 and d3)]:
    print(f'{tag} {text} -> {"held" if ok else "failed"}')
