"""G58 registered analysis (committed with the predictions, before the run). Run from the repo root:
    python3 gates/gate58/referee/analyze.py <dir with probe_<arm>.json[.gz], sheet.json>
Right_X = of the declared decisions, the share sheet X states right (D before review; SL after the list review; CB after
SL's list review plus the spot checks, each correction applied alone and its case shown again).
V1: right_CB − right_SL ≥ +0.12.    V2: hp_CB ≥ hp_SL + 5.    V3: of the corrected cases re-shown, ≥ 80% are confirmed.
V4: CB spoils at most 1 decision SL had right.
Ship (the combined review becomes Hive's review for a skimming owner): V1 and V2 hold.
Kill: hp_CB ≤ hp_SL and right_CB ≤ right_SL."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'SL', 'CB')
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
rng = random.Random(58)
dd = [100 * (F['CB'][c] - F['SL'][c]) for c in cats]
bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
print(f'CB − SL = {sum(dd) / len(dd):+.1f} points (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f})')
w = json.load(open(os.path.join(d, 'sheet.json'))); L = w['labels']; n = len(L)
right = {a: sum(x[a] == 'right' for x in L) / n for a in ('D', 'SL', 'CB', 'R')}
for a in ('D', 'SL', 'CB', 'R'):
    c = collections.Counter(x[a] for x in L)
    print(f'{a}: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')) + f'  (right {right[a]:.2f})')
spoiled = sum(x['SL'] == 'right' and x['CB'] != 'right' for x in L)
cb = w['reviews']['CB']; sl = w['reviews']['SL']
fx = cb['fixes']; reshown = [f for f in fx if f.get('now')]; conf = sum(1 for f in reshown if f.get('confirmed'))
cshare = conf / max(1, len(reshown))
print(f"SL: {sl['replies']} replies, {sl['minutes']} min; CB spots: {len(cb['shown'])} shown "
      f"({len(cb['skipped_functions'])} functions skipped as changed by the list), {len(fx)} corrected, {len(reshown)} re-shown, "
      f"{conf} confirmed ({cshare:.2f}); sheet lengths D {len(w['D'])}, SL {len(sl['rules'])}, CB {len(cb['rules'])}")
print('\npredictions')
for tag, text, held in [
        ('V1', f'right_CB − right_SL ≥ +0.12: {right["CB"] - right["SL"]:+.2f}', right['CB'] - right['SL'] >= .12),
        ('V2', f'CB ≥ SL + 5 hidden: {hp["CB"] - hp["SL"]:+.1f}', hp['CB'] - hp['SL'] >= 5),
        ('V3', f'≥ 80% of re-shown corrections confirmed: {cshare:.2f} ({conf} of {len(reshown)})', cshare >= .8 and len(reshown) > 0),
        ('V4', f'CB spoils ≤ 1 decision SL had right: {spoiled}', spoiled <= 1)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Ship the combined review: {"FIRED" if right["CB"] - right["SL"] >= .12 and hp["CB"] - hp["SL"] >= 5 else "did not fire"}')
print(f'Kill: {"FIRED" if hp["CB"] <= hp["SL"] and right["CB"] <= right["SL"] else "did not fire"}')
