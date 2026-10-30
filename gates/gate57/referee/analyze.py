"""G57 registered analysis (committed with the predictions, before the run). Run from the repo root:
    python3 gates/gate57/referee/analyze.py <dir with probe_<arm>.json[.gz], sheet.json>
Right_X = of the 25 declared decisions, the share sheet X states right (D before review; SL after the list review; SP
after the spot checks, corrections applied).
U1: right_SP − right_SL ≥ +0.15.    U2: hp_SP ≥ hp_SL + 5.    U3: the skimmer corrects ≥ 25% of the spot checks.
U4: SP spoils at most 1 decision D had right.
Ship (spot checks become Hive's review for an owner who skims): U1 and U2 hold.   Kill: hp_SP ≤ hp_SL and right_SP ≤ right_SL."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'SL', 'SP')
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
rng = random.Random(57)
dd = [100 * (F['SP'][c] - F['SL'][c]) for c in cats]
bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
print(f'SP − SL = {sum(dd) / len(dd):+.1f} points (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f})')
w = json.load(open(os.path.join(d, 'sheet.json'))); L = w['labels']; n = len(L)
right = {a: sum(x[a] == 'right' for x in L) / n for a in ('D', 'SL', 'SP', 'R')}
for a in ('D', 'SL', 'SP', 'R'):
    c = collections.Counter(x[a] for x in L)
    print(f'{a}: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')) + f'  (right {right[a]:.2f})')
spoiled = sum(x['D'] == 'right' and x['SP'] != 'right' for x in L)
sp = w['reviews']['SP']; sl = w['reviews']['SL']
share = len(sp['fixes']) / max(1, len(sp['spots']))
print(f"SL: {sl['replies']} replies, {sl['minutes']} min; SP: {len(sp['spots'])} spot checks, {len(sp['fixes'])} corrected "
      f"({share:.2f}), {sp['minutes']} min; sheet lengths D {len(w['D'])}, SP {len(sp['rules'])}")
print('\npredictions')
for tag, text, held in [
        ('U1', f'right_SP − right_SL ≥ +0.15: {right["SP"] - right["SL"]:+.2f}', right['SP'] - right['SL'] >= .15),
        ('U2', f'SP ≥ SL + 5 hidden: {hp["SP"] - hp["SL"]:+.1f}', hp['SP'] - hp['SL'] >= 5),
        ('U3', f'the skimmer corrects ≥ 25% of spot checks: {share:.2f}', share >= .25),
        ('U4', f'SP spoils ≤ 1 decision D had right: {spoiled}', spoiled <= 1)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Ship spot checks: {"FIRED" if right["SP"] - right["SL"] >= .15 and hp["SP"] - hp["SL"] >= 5 else "did not fire"}')
print(f'Kill: {"FIRED" if hp["SP"] <= hp["SL"] and right["SP"] <= right["SL"] else "did not fire"}')
