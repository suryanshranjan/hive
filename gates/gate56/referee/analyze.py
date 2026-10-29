"""G56 registered analysis (committed with the predictions, before the run). Run from the repo root:
    python3 gates/gate56/referee/analyze.py <dir with probe_<arm>.json[.gz], sheet.json>
Right_X = of the 25 declared decisions, the share sheet X states right. D/DS are the sheets before review, SF/SS after.
T1: the short sheet has ≤ 35 rules.       T2: right_SS − right_SF ≥ +0.15 (the skimmer ends with more decisions right).
T3: hp_SS ≥ hp_SF + 5.                    T4: the short sheet addresses ≥ 70% of the decisions before review (DS not absent).
Ship (the describer writes the short sheet by default, the full one a tap away): T2 and T3 hold.
Kill: hp_SS ≤ hp_SF and right_SS ≤ right_SF."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'SF', 'SS')
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
rng = random.Random(56)
dd = [100 * (F['SS'][c] - F['SF'][c]) for c in cats]
bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
print(f'SS − SF = {sum(dd) / len(dd):+.1f} points (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f})')
w = json.load(open(os.path.join(d, 'sheet.json'))); L = w['labels']; n = len(L)
right = {a: sum(x[a] == 'right' for x in L) / n for a in ('D', 'DS', 'SF', 'SS', 'R')}
for a in ('D', 'DS', 'SF', 'SS', 'R'):
    c = collections.Counter(x[a] for x in L)
    print(f'{a}: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')) + f'  (right {right[a]:.2f})')
for a in ('SF', 'SS'):
    r = w['reviews'][a]; print(f'{a}: {r.get("replies")} replies, {r.get("minutes")} min' + (' (REVIEW ERROR)' if r.get('error') else ''))
print(f'sheet lengths: D {len(w["D"])}, DS {len(w["DS"])}')
addressed = sum(x['DS'] != 'absent' for x in L) / n
print('\npredictions')
for tag, text, held in [
        ('T1', f'short sheet ≤ 35 rules: {len(w["DS"])}', len(w['DS']) <= 35),
        ('T2', f'right_SS − right_SF ≥ +0.15: {right["SS"] - right["SF"]:+.2f}', right['SS'] - right['SF'] >= .15),
        ('T3', f'SS ≥ SF + 5 hidden: {hp["SS"] - hp["SF"]:+.1f}', hp['SS'] - hp['SF'] >= 5),
        ('T4', f'short sheet addresses ≥ 70% before review: {addressed:.2f}', addressed >= .7)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Ship short sheets: {"FIRED" if right["SS"] - right["SF"] >= .15 and hp["SS"] - hp["SF"] >= 5 else "did not fire"}')
print(f'Kill: {"FIRED" if hp["SS"] <= hp["SF"] and right["SS"] <= right["SF"] else "did not fire"}')
