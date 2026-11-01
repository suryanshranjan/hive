"""G78 registered analysis (committed with the predictions, before any run):
    python3 gates/gate78/referee/analyze.py runs/g78_H1 runs/g78_HM1 runs/g78_HM2 runs/g78_H2
M1 each HM run: >= 3 of 4 builders ran graphify      M2 HM cost <= 0.85x H        M3 HM time to accuracy <= 0.85x H
M4 HM final hidden >= H - 3 (of 61)                  M5 HM reads+searches per builder <= 0.8x H
Time to accuracy: minutes to the first landing with >= 55 of 61 hidden, else the wall minutes.
Claim: (M2 or M3) and M4."""
import json, os, sys
from statistics import mean
R = [json.load(open(os.path.join(d, 'result.json'))) for d in sys.argv[1:]]
def tacc(r):
    hit = [l['minute'] for l in r['landings'] if l['hidden'] >= 55]
    return hit[0] if hit else r['wall_minutes']
def nav(r):
    t = r['tools'].values(); return sum(x['Read'] + x['Grep'] + x['Glob'] + x['search_bash'] for x in t) / max(1, len(r['tools']))
def users(r): return sum(1 for x in r['tools'].values() if x['graphify'] > 0)
for r in R:
    print(f"{r['arm']}{r['k']}: hidden {r['hidden_passed']}/{r['hidden_total']} (other failures {r['other_failures']}), "
          f"time to accuracy {tacc(r)} min, wall {r['wall_minutes']} min, cost ${r['cost']}, tokens {r['tokens']:,}, "
          f"reads+searches/builder {nav(r):.1f}, graphify users {users(r)} ({sum(x['graphify'] for x in r['tools'].values())} calls), "
          f"landings {len(r['landings'])}, prep {r['prep_seconds']} s, leaks {sum(len(x['outside']) for x in r['tools'].values())}")
H = [r for r in R if r['arm'] == 'H']; M = [r for r in R if r['arm'] == 'HM']
m = lambda rs, f: mean(f(r) for r in rs)
c = (m(H, lambda r: r['cost']), m(M, lambda r: r['cost'])); t = (m(H, tacc), m(M, tacc))
h = (m(H, lambda r: r['hidden_passed']), m(M, lambda r: r['hidden_passed'])); n = (m(H, nav), m(M, nav))
print(f"\nH:  hidden {h[0]:.1f}, time to accuracy {t[0]:.1f} min, cost ${c[0]:.2f}, reads+searches/builder {n[0]:.1f}")
print(f"HM: hidden {h[1]:.1f}, time to accuracy {t[1]:.1f} min, cost ${c[1]:.2f}, reads+searches/builder {n[1]:.1f}")
m1 = all(users(r) >= 3 for r in M); m2 = c[1] <= 0.85 * c[0]; m3 = t[1] <= 0.85 * t[0]; m4 = h[1] >= h[0] - 3; m5 = n[1] <= 0.8 * n[0]
print('\npredictions')
for tag, text, ok in [('M1', f"each HM run: >= 3 of 4 used graphify ({[users(r) for r in M]})", m1),
                      ('M2', f"HM cost {c[1]:.2f} <= 0.85 x H {c[0]:.2f} (ratio {c[1]/c[0]:.2f})", m2),
                      ('M3', f"HM time to accuracy {t[1]:.1f} <= 0.85 x H {t[0]:.1f} (ratio {t[1]/t[0]:.2f})", m3),
                      ('M4', f"HM hidden {h[1]:.1f} >= H {h[0]:.1f} - 3", m4),
                      ('M5', f"HM reads+searches {n[1]:.1f} <= 0.8 x H {n[0]:.1f} (ratio {n[1]/n[0]:.2f})", m5),
                      ('Claim', '(M2 or M3) and M4', (m2 or m3) and m4)]:
    print(f'{tag} {text} -> {"held" if ok else "failed"}')
