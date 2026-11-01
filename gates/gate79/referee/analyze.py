"""G79 registered analysis (committed with the predictions, before any run):
    python3 gates/gate79/referee/analyze.py runs/g79_H1 runs/g79_HG1 runs/g79_HG2 runs/g79_H2 runs/g79_H3 runs/g79_HG3
Time to accuracy: minutes from the start of prepare (so the map's build counts) to the first landing with >= 23 of 25
hidden, else prepare plus the wall minutes.
G1 each HG run: >= 3 of 4 builders ran graphify     G2 HG cost <= 0.85x H      G3 HG time to accuracy <= 0.85x H
G4 HG final hidden >= H - 2 (of 25)                G5 HG reads+searches per builder <= 0.8x H
Claim: G1 and (G2 or G3) and G4."""
import json, os, sys
from statistics import mean
R = [json.load(open(os.path.join(d, 'result.json'))) for d in sys.argv[1:]]
def tacc(r):
    hit = [l['minute'] for l in r['landings'] if l['hidden'] >= 23]
    return round(r['prep_seconds'] / 60 + (hit[0] if hit else r['wall_minutes']), 1)
def nav(r):
    return sum(x['Read'] + x['Grep'] + x['Glob'] + x['search_bash'] for x in r['tools'].values()) / max(1, len(r['tools']))
def users(r): return sum(1 for x in r['tools'].values() if x['graphify'] > 0)
for r in R:
    print(f"{r['arm']}{r['k']}: hidden {r['hidden_passed']}/{r['hidden_total']} (other failures {r['other_failures']}), "
          f"time to accuracy {tacc(r)} min, wall {r['wall_minutes']} min, prep {r['prep_seconds']} s, cost ${r['cost']}, "
          f"tokens {r['tokens']:,}, reads+searches/builder {nav(r):.1f}, graphify users {users(r)} "
          f"({sum(x['graphify'] for x in r['tools'].values())} calls), landings {len(r['landings'])}, "
          f"leaks {sum(len(x['outside']) for x in r['tools'].values())}")
H = [r for r in R if r['arm'] == 'H']; G = [r for r in R if r['arm'] == 'HG']
m = lambda rs, f: mean(f(r) for r in rs)
c = (m(H, lambda r: r['cost']), m(G, lambda r: r['cost'])); t = (m(H, tacc), m(G, tacc))
h = (m(H, lambda r: r['hidden_passed']), m(G, lambda r: r['hidden_passed'])); n = (m(H, nav), m(G, nav))
print(f"\nH:  hidden {h[0]:.2f}, time to accuracy {t[0]:.1f} min, cost ${c[0]:.2f}, reads+searches/builder {n[0]:.1f}")
print(f"HG: hidden {h[1]:.2f}, time to accuracy {t[1]:.1f} min, cost ${c[1]:.2f}, reads+searches/builder {n[1]:.1f}")
g1 = all(users(r) >= 3 for r in G); g2 = c[1] <= 0.85 * c[0]; g3 = t[1] <= 0.85 * t[0]; g4 = h[1] >= h[0] - 2
g5 = n[1] <= 0.8 * n[0] if n[0] else False
print('\npredictions')
for tag, text, ok in [('G1', f"each HG run: >= 3 of 4 used graphify ({[users(r) for r in G]})", g1),
                      ('G2', f"HG cost {c[1]:.2f} <= 0.85 x H {c[0]:.2f} (ratio {c[1]/c[0]:.2f})", g2),
                      ('G3', f"HG time to accuracy {t[1]:.1f} <= 0.85 x H {t[0]:.1f} (ratio {t[1]/t[0]:.2f})", g3),
                      ('G4', f"HG hidden {h[1]:.2f} >= H {h[0]:.2f} - 2", g4),
                      ('G5', f"HG reads+searches {n[1]:.1f} <= 0.8 x H {n[0]:.1f}", g5),
                      ('Claim', 'G1 and (G2 or G3) and G4', g1 and (g2 or g3) and g4)]:
    print(f'{tag} {text} -> {"held" if ok else "failed"}')
