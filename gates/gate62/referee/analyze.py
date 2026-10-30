"""G62 registered analysis (committed with the predictions, before the run):
    python3 gates/gate62/referee/analyze.py runs/g62a runs/g62b
recall(X) = of the 300 prober calls where Gate 60's N0 differs from the policy, the share where wing X's result differs from
N0's; precision(X) = of the calls where X differs from N0, the share where N0 is wrong. Pooled over both runs.
G1  Haiku's recall >= 0.35          G2  Opus's recall >= the Sonnet replicate's + 0.10
G3  the Sonnet replicate's recall is within 0.10 of Gate 60's B (a check that same-model overlap is stable)
G4  every wing with recall >= 0.35 has precision >= 0.50
Go (a new owner test with that wing as the second build): some other-model wing reaches recall >= 0.50 with precision >= 0.50.
Stop (two wings is not worth an owner test): no wing reaches recall 0.35."""
import collections, gzip, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '..', 'gate60', 'referee'))
import wings
tot = collections.defaultdict(collections.Counter)
for d in sys.argv[1:]:
    r = json.load(open(os.path.join(d, 'results.json')))
    out = {w: json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
           for w, p in ((w, os.path.join(d, f'out_{w}.json')) for w in ('N0', 'B', 'So', 'Op', 'Ha', 'policy'))}
    A, O = out['N0'], out['policy']
    wrong = {i for i, (a, o) in enumerate(zip(A, O)) if a and o and not wings.same(a, o)}
    print(f"== {d} ({r['src']}): N0 wrong on {len(wrong)} of {len(A)} calls; hidden calls right: "
          + ', '.join(f"{w} {v['hidden_calls_right']}/{v['hidden_calls']}" for w, v in r['wings'].items()))
    for w in ('B', 'So', 'Op', 'Ha'):
        X = out[w]; dis = {i for i, (a, x) in enumerate(zip(A, X)) if a and x and not wings.same(a, x)}
        t = tot[w]; t['wrong'] += len(wrong); t['caught'] += len(wrong & dis); t['dis'] += len(dis); t['dis_wrong'] += len(dis & wrong)
        print(f'  {w}: disagrees on {len(dis)}; recall {len(wrong & dis) / max(1, len(wrong)):.2f}; precision {len(dis & wrong) / max(1, len(dis)):.2f}')
    union = set()
    for w in ('So', 'Op', 'Ha'):
        union |= {i for i, (a, x) in enumerate(zip(A, out[w])) if a and x and not wings.same(a, x)}
    tot['union']['wrong'] += len(wrong); tot['union']['caught'] += len(wrong & union); tot['union']['dis'] += len(union)
    tot['union']['dis_wrong'] += len(union & wrong)
rc = {w: t['caught'] / max(1, t['wrong']) for w, t in tot.items()}; pr = {w: t['dis_wrong'] / max(1, t['dis']) for w, t in tot.items()}
print('\n== pooled')
for w in ('B', 'So', 'Op', 'Ha', 'union'):
    print(f"{w}: recall {rc[w]:.2f} ({tot[w]['caught']} of {tot[w]['wrong']}), precision {pr[w]:.2f}, disagreements {tot[w]['dis']}")
res = [('G1', f"Haiku recall ≥ 0.35: {rc['Ha']:.2f}", rc['Ha'] >= .35),
       ('G2', f"Opus recall ≥ Sonnet replicate + 0.10: {rc['Op']:.2f} vs {rc['So']:.2f}", rc['Op'] >= rc['So'] + .10),
       ('G3', f"Sonnet replicate within 0.10 of B: {rc['So']:.2f} vs {rc['B']:.2f}", abs(rc['So'] - rc['B']) <= .10),
       ('G4', 'wings with recall ≥ 0.35 have precision ≥ 0.50: ' + ', '.join(f'{w} {pr[w]:.2f}' for w in ('So', 'Op', 'Ha') if rc[w] >= .35),
        all(pr[w] >= .5 for w in ('So', 'Op', 'Ha') if rc[w] >= .35))]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Go: {'FIRED (' + ', '.join(w for w in ('Op', 'Ha') if rc[w] >= .5 and pr[w] >= .5) + ')' if any(rc[w] >= .5 and pr[w] >= .5 for w in ('Op', 'Ha')) else 'did not fire'}")
print(f"Stop: {'FIRED' if all(rc[w] < .35 for w in ('So', 'Op', 'Ha')) else 'did not fire'}")
