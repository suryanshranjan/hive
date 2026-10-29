"""G55 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python3 gates/gate55/referee/analyze.py <dir with probe_<arm>.json[.gz], sheet.json>
Repair rate of a review = of the declared decisions sheet D (from N0's code) states wrongly or partly, the share the
reviewed sheet states right. Spoiled = right in D, not right after the review. Added = absent in D, right after.
S1: the careful list review (CC) repairs ≥ 0.80.            S2: the skimming list review (CS) repairs ≤ 0.50.
S3: the skimming owner repairs ≥ 0.15 more in the conversation (CT) than with the list (CS).
S4: hp_CT ≥ hp_CS + 5.                                       S5: hp_CC ≥ 95.
Model check: S2 fails with CS ≥ 0.80 → the skimming brief did not change behaviour; the gate says nothing about attention."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'CC', 'CS', 'CT')
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
P = {a: load(os.path.join(d, f'probe_{a}.json')) for a in arms}
cats = sorted({r['cat'] for r in P['N0']})
def per_fn(a):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P[a]: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in cats}
F = {a: per_fn(a) for a in arms}
hp = {a: 100 * sum(F[a].values()) / len(cats) for a in arms}
print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in arms))
rng = random.Random(55)
def paired(a, b):
    dd = [100 * (F[a][c] - F[b][c]) for c in cats]
    bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
    return sum(dd) / len(dd), bs[100], bs[3899]
for a, b in (('CC', 'N0'), ('CS', 'N0'), ('CT', 'N0'), ('CT', 'CS'), ('CC', 'CT')):
    m, lo, hi = paired(a, b); print(f'{a} − {b} = {m:+.1f} points (95% CI {lo:+.1f} to {hi:+.1f})')
w = json.load(open(os.path.join(d, 'sheet.json'))); L = w['labels']
bad = [x for x in L if x['D'] in ('wrong', 'partial')]; absent = [x for x in L if x['D'] == 'absent']
rep = {}
for a in ('CC', 'CS', 'CT', 'R'):
    c = collections.Counter(x[a] for x in L)
    rep[a] = sum(x[a] == 'right' for x in bad) / len(bad) if bad else float('nan')
    spoiled = sum(x['D'] == 'right' and x[a] != 'right' for x in L); added = sum(x[a] == 'right' for x in absent)
    r = w['reviews'].get(a, {})
    print(f'{a}: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')) +
          f'; repaired {sum(x[a] == "right" for x in bad)}/{len(bad)} ({rep[a]:.2f}); added {added}/{len(absent)}; spoiled {spoiled}'
          + (f'; {r.get("replies")} replies, {r.get("minutes")} min' if r else '') + (' (REVIEW ERROR)' if r.get('error') else ''))
print(f'D: {len(w["D"])} rules; ' + ', '.join(f'{v} {collections.Counter(x["D"] for x in L)[v]}' for v in ('right', 'partial', 'wrong', 'absent')))
print('\npredictions')
for tag, text, held in [
        ('S1', f'careful list repairs ≥ 0.80: {rep["CC"]:.2f}', rep['CC'] >= .8),
        ('S2', f'skimming list repairs ≤ 0.50: {rep["CS"]:.2f}', rep['CS'] <= .5),
        ('S3', f'conversation repairs ≥ 0.15 more for the skimmer: {rep["CT"] - rep["CS"]:+.2f}', rep['CT'] - rep['CS'] >= .15),
        ('S4', f'CT ≥ CS + 5 points: {hp["CT"] - hp["CS"]:+.1f}', hp['CT'] - hp['CS'] >= 5),
        ('S5', f'CC ≥ 95%: {hp["CC"]:.1f}', hp['CC'] >= 95)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Model check (skimming brief changed nothing, CS ≥ 0.80): {"FIRED" if rep["CS"] >= .8 else "did not fire"}')
