"""G40 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python3 gates/gate40/referee/analyze.py <dir with probe_<arm>.json[.gz], wind_tunnel.json>
hp_X = hidden pass of team X (points, mean over functions). Share fixed = edge calls wrong in N0 and right in X, over
N0's wrong edge calls (Gate 15's definition). Coverage = declared decisions the judge marks asked in that interview.
Transfer = of those asked, the share its sheet states right.
G1: coverage H2 ≥ 0.85 and coverage H ≤ 0.75.     G2: hp_H2 − hp_H ≥ +8 (paired by function, bootstrap CI reported).
G3: transfer ≥ 0.85 for both H and H2.            G4: hp_R ≥ 95.      G5: hp_R − hp_T ≥ +10.
G6: owner replies in H2 ≤ 1.6 × those in H.        G7: hp_N0 < 65.
Kill: hp_H2 ≤ hp_H → the planner change does not ship.
Ship: hp_H2 − hp_H ≥ +5 and coverage H2 > coverage H → the planner lists unusual input by default."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'H', 'H2', 'R', 'T')
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
for a in arms[1:]:
    s, n = share(a); g = [k for k, v in ok['N0'].items() if v]
    print(f'{a}: fixes {s:.2f} of {n} N0 edge errors; breaks {sum(not ok[a][k] for k in g)} of {len(g)} N0-right edge calls')
rng = random.Random(40)
dd = [100 * (F['H2'][c] - F['H'][c]) for c in cats]
bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
diff = sum(dd) / len(dd)
print(f'H2 − H = {diff:+.1f} points (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f}, bootstrap over functions)')

w = json.load(open(os.path.join(d, 'wind_tunnel.json'))); L = w['labels']; iv = w['interviews']
cov, tr = {}, {}
for a in ('H', 'H2'):
    asked = [x for x in L if x[f'asked_{a}']]
    cov[a] = len(asked) / len(L); tr[a] = sum(x[a] == 'right' for x in asked) / len(asked) if asked else float('nan')
    c = collections.Counter(x[a] for x in L)
    print(f'{a}: {len(iv[a]["planned_decisions"])} planned decisions, {len(iv[a]["questions"])} questions, '
          f'{iv[a]["owner_replies"]} owner replies, {len(iv[a]["rules"])} rules; asked {len(asked)} of {len(L)} '
          f'({cov[a]:.2f}); of those stated right {tr[a]:.2f}; sheet: ' +
          ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')))
c = collections.Counter(x['R'] for x in L)
print('R sheet: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')) + f'; {len(w["R"])} rules')
print('\nper function: N0 edge errors, share fixed by H / H2 / R / T, labels H | H2')
for f in cats:
    s = [share(a, {f})[0] for a in ('H', 'H2', 'R', 'T')]
    print(f'  {f:24s} {share("H", {f})[1]:3d}  ' + ' / '.join('  – ' if x != x else f'{x:.2f}' for x in s) + '   '
          + ' '.join(x['H'][0] for x in L if x['function'] == f) + ' | ' + ' '.join(x['H2'][0] for x in L if x['function'] == f))

print('\npredictions')
r = iv['H2']['owner_replies'] / max(1, iv['H']['owner_replies'])
for tag, text, held in [
        ('G1', f'coverage H2 ≥ 0.85 and H ≤ 0.75: {cov["H2"]:.2f}, {cov["H"]:.2f}', cov['H2'] >= .85 and cov['H'] <= .75),
        ('G2', f'H2 − H ≥ +8: {diff:+.1f}', diff >= 8),
        ('G3', f'transfer ≥ 0.85 in H and H2: {tr["H"]:.2f}, {tr["H2"]:.2f}', tr['H'] >= .85 and tr['H2'] >= .85),
        ('G4', f'R ≥ 95%: {hp["R"]:.1f}', hp['R'] >= 95),
        ('G5', f'R − T ≥ +10: {hp["R"] - hp["T"]:+.1f}', hp['R'] - hp['T'] >= 10),
        ('G6', f'owner replies H2 ≤ 1.6 × H: {iv["H2"]["owner_replies"]} vs {iv["H"]["owner_replies"]} ({r:.2f}×)', r <= 1.6),
        ('G7', f'N0 < 65%: {hp["N0"]:.1f}', hp['N0'] < 65)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Kill H2 ≤ H: {"FIRED" if hp["H2"] <= hp["H"] else "did not fire"}')
print(f'Ship rule (H2 − H ≥ +5 and coverage up): {"FIRED" if diff >= 5 and cov["H2"] > cov["H"] else "did not fire"}')
