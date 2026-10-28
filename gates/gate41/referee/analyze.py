"""G41 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python3 gates/gate41/referee/analyze.py <dir with probe_<arm>.json[.gz], wind_tunnel.json>
hp_X = hidden pass (points, mean over functions). Share fixed / broken as in Gates 39-40.
Kept_X = of the declared decisions asked (an answered question is about it), the share hand-over X states right.
K1: hp_K − hp_H ≥ +5 (paired by function, bootstrap CI reported).   K2: kept_K ≥ 0.90 and kept_H ≤ 0.80.
K3: K breaks at most 5 more N0-right edge calls than H.                K4: hp_R ≥ 95.
K5: of the asked decisions, his answers convey ≥ 0.85 right (the loss is Hive's, not the owner's wording).
K6: N0 < 65.        Kill: hp_K ≤ hp_H.        Ship: hp_K − hp_H ≥ +5 → Hive hands builders every ruling whole."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'H', 'K', 'R')
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
P = {a: load(os.path.join(d, f'probe_{a}.json')) for a in arms}
key = lambda r: (r['cat'], r['test'], r['q'])
ok = {a: {key(r): r['ok'] for r in P[a] if r['kind'] == 'edge'} for a in arms}
cats = sorted({r['cat'] for r in P['N0']})
def per_fn(a):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P[a]: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in cats}
F = {a: per_fn(a) for a in arms}
hp = {a: 100 * sum(F[a].values()) / len(cats) for a in arms}
print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in arms))
def share(a, fs=None):
    e = [k for k, v in ok['N0'].items() if not v and (fs is None or k[0] in fs)]
    return (sum(ok[a][k] for k in e) / len(e) if e else float('nan')), len(e)
brk = {}
for a in arms[1:]:
    s, n = share(a); g = [k for k, v in ok['N0'].items() if v]; brk[a] = sum(not ok[a][k] for k in g)
    print(f'{a}: fixes {s:.2f} of {n} N0 edge errors; breaks {brk[a]} of {len(g)} N0-right edge calls')
rng = random.Random(41)
dd = [100 * (F['K'][c] - F['H'][c]) for c in cats]
bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
diff = sum(dd) / len(dd)
print(f'K − H = {diff:+.1f} points (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f}, bootstrap over functions)')

w = json.load(open(os.path.join(d, 'wind_tunnel.json'))); L = w['labels']; iv = w['interview']
asked = [x for x in L if x['asked']]
kept = {a: (sum(x[a] == 'right' for x in asked) / len(asked) if asked else float('nan')) for a in ('H', 'K', 'R')}
ans = sum(x['answer'] == 'right' for x in asked) / len(asked) if asked else float('nan')
print(f'interview: {len(iv["questions"])} questions, {len(iv["skipped"])} skipped as settled, {iv["owner_replies"]} owner '
      f'replies; {len(iv["rules"])} sheet rules, {len(iv["rulings"])} rulings')
print(f'decisions: asked {len(asked)} of {len(L)}; only in skipped questions {sum(x["skipped_only"] for x in L)}; '
      f'his answers right on {sum(x["answer"] == "right" for x in asked)} of the asked ({ans:.2f})')
for a in ('H', 'K', 'R'):
    c = collections.Counter(x[a] for x in L)
    print(f'{a}: kept {kept[a]:.2f} of asked; all decisions: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')))
print('\nwhere the asked decisions were lost (his answer -> H -> K):')
for x in asked:
    if x['H'] != 'right' or x['K'] != 'right' or x['answer'] != 'right':
        print(f'  {x["function"]} {x["decision"]} {x["label"][:40]:40s} answer {x["answer"]:8s} H {x["H"]:8s} K {x["K"]:8s} {x["note"][:50]}')
print('\nper function: N0 edge errors, share fixed by H / K / R')
for f in cats:
    s = [share(a, {f})[0] for a in ('H', 'K', 'R')]
    print(f'  {f:24s} {share("H", {f})[1]:3d}  ' + ' / '.join('  – ' if x != x else f'{x:.2f}' for x in s))

print('\npredictions')
for tag, text, held in [
        ('K1', f'K − H ≥ +5: {diff:+.1f}', diff >= 5),
        ('K2', f'kept K ≥ 0.90 and H ≤ 0.80: {kept["K"]:.2f}, {kept["H"]:.2f}', kept['K'] >= .9 and kept['H'] <= .8),
        ('K3', f'K breaks ≤ H + 5: {brk["K"]} vs {brk["H"]}', brk['K'] <= brk['H'] + 5),
        ('K4', f'R ≥ 95%: {hp["R"]:.1f}', hp['R'] >= 95),
        ('K5', f'his answers right on ≥ 0.85 of asked: {ans:.2f}', ans >= .85),
        ('K6', f'N0 < 65%: {hp["N0"]:.1f}', hp['N0'] < 65)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Kill K ≤ H: {"FIRED" if hp["K"] <= hp["H"] else "did not fire"}')
print(f'Ship rule (K − H ≥ +5): {"FIRED" if diff >= 5 else "did not fire"}')
