"""G61 registered analysis (committed with the predictions, before the run):
    python3 gates/gate61/referee/analyze.py runs/g61/results.json
broke share = of the hidden calls build 1 had right, the share a team's build 2 gets wrong.
F1  at least one N team breaks >= 2% of them (without the log, the clean-up breaks confirmed behaviour)
F2  T's mean broke share <= half of N's
F3  T's mean hidden pass on the old functions >= N's + 2 points
F4  all 6 teams finish the clean-up (business.py, the three old files gone)
Ship (Hive keeps confirmed outcomes as tests in the project's suite): F2 and F3.
Kill: N's mean broke share < 1% (builders did not break confirmed behaviour without the log)."""
import json, sys
r = json.load(open(sys.argv[1])); T = r['teams']
print(f"build 1: {r['build1']['right']}/{r['build1']['calls']} hidden calls right; flight log {r['flight_log']['tests']} tests "
      f"over {len(r['flight_log']['per_function'])} functions ({r['flight_log']['dropped']} cases dropped)")
share = {t: v['broke'] / max(1, v['build1_right']) for t, v in T.items()}
hp = {t: 100 * v['right'] / v['calls'] for t, v in T.items()}
for t, v in sorted(T.items()):
    print(f"{t}: hidden {hp[t]:.1f}%, broke {v['broke']} ({100 * share[t]:.1f}%), invoice_total {v['invoice_right']}/{v['invoice_calls']}, "
          f"clean-up {'done' if v['cleanup'] else 'not done'}, {v['commits']} commits")
m = lambda d, a: sum(x for t, x in d.items() if T[t]['arm'] == a) / sum(1 for t in T if T[t]['arm'] == a)
sN, sT, hN, hT = m(share, 'N'), m(share, 'T'), m(hp, 'N'), m(hp, 'T')
print(f'mean broke share: N {100 * sN:.1f}%, T {100 * sT:.1f}%; mean hidden: N {hN:.1f}%, T {hT:.1f}%')
res = [('F1', f"an N team breaks ≥ 2%: max {100 * max(share[t] for t in T if T[t]['arm'] == 'N'):.1f}%",
        max(share[t] for t in T if T[t]['arm'] == 'N') >= .02),
       ('F2', f'T broke share ≤ half of N: {100 * sT:.1f}% vs {100 * sN:.1f}%', sT <= sN / 2 and sN > 0),
       ('F3', f'T hidden ≥ N + 2: {hT - hN:+.1f}', hT - hN >= 2),
       ('F4', f"all 6 teams finish the clean-up: {sum(v['cleanup'] for v in T.values())} of 6", all(v['cleanup'] for v in T.values()))]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
ok = {t: h for t, _, h in res}
print(f"Ship (the flight log): {'FIRED' if ok['F2'] and ok['F3'] else 'did not fire'}")
print(f"Kill: {'FIRED' if sN < .01 else 'did not fire'}")
