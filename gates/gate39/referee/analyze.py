"""G39 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python3 gates/gate39/referee/analyze.py <dir with probe_<arm>.json[.gz], summary.json, wind_tunnel.json>
hp_X = hidden pass of team X (points). Share fixed = edge calls wrong in N0 and right in X, over N0's wrong edge calls
(Gate 15's definition). K = (hp_H − hp_N0) / (hp_T − hp_N0): the share of the owner's-tour gain Hive's interview keeps.
W1: share fixed by T ≥ 0.85.     W2: hp_R ≥ hp_T − 5.     W3: 0.40 ≤ K ≤ 0.80.
W4: the interview asks about ≥ 50% and ≤ 85% of the declared decisions; of those asked, sheet H states ≥ 80% right.
W5: hp_N0 < 65%.                 Kill: K < 0.25.
Decision rules: K ≥ 0.85 → the interview is not the leak with a consistent owner. Coverage < 0.6 with transfer ≥ 0.8 →
the leak is what Hive asks. Transfer < 0.7 → the leak is writing answers as rules. hp_R < hp_T − 10 → complete prose
rules still lose to examples."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'H', 'R', 'T')
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
P = {a: load(os.path.join(d, f'probe_{a}.json')) for a in arms}
key = lambda r: (r['cat'], r['test'], r['q'])
ok = {a: {key(r): r['ok'] for r in P[a] if r['kind'] == 'edge'} for a in arms}
cats = sorted({r['cat'] for r in P['N0']})
def per_fn(a):   # hidden pass per function: a test passes when all its calls pass
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P[a]: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in cats}
F = {a: per_fn(a) for a in arms}
hp = {a: 100 * sum(F[a].values()) / len(cats) for a in arms}
print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in arms))

def share(a, fs=None):
    e = [k for k, v in ok['N0'].items() if not v and (fs is None or k[0] in fs)]
    return (sum(ok[a][k] for k in e) / len(e) if e else float('nan')), len(e)
def broken(a):
    g = [k for k, v in ok['N0'].items() if v]
    return sum(not ok[a][k] for k in g), len(g)
for a in arms[1:]:
    s, n = share(a); b, m = broken(a)
    print(f'{a}: fixes {s:.2f} of {n} N0 edge errors; breaks {b} of {m} N0-right edge calls')

rng = random.Random(39)
def K(fs):
    gT = sum(F['T'][c] - F['N0'][c] for c in fs); gH = sum(F['H'][c] - F['N0'][c] for c in fs)
    return gH / gT if gT else float('nan')
k = K(cats); bs = sorted(K([rng.choice(cats) for _ in cats]) for _ in range(4000))
bs = [x for x in bs if x == x]
print(f'K = (H − N0)/(T − N0) = {k:.2f} (95% CI {bs[int(.025 * len(bs))]:.2f} to {bs[int(.975 * len(bs)) - 1]:.2f}, bootstrap over functions)')
kr = sum(F['R'][c] - F['N0'][c] for c in cats) / sum(F['T'][c] - F['N0'][c] for c in cats)
print(f'R keeps {kr:.2f} of the tour gain')

w = json.load(open(os.path.join(d, 'wind_tunnel.json'))); L = w['labels']
asked = [x for x in L if x['asked']]
cov = len(asked) / len(L)
tr = sum(x['H'] == 'right' for x in asked) / len(asked) if asked else float('nan')
print(f'interview: {len(w["questions"])} questions, {w["owner_replies"]} owner replies, {w["interview_minutes"]} min; '
      f'{len(w["H"])} H rules, {len(w["R"])} R rules')
print(f'coverage: asked about {len(asked)} of {len(L)} declared decisions ({cov:.2f}); of those, H states '
      f'{sum(x["H"] == "right" for x in asked)} right ({tr:.2f})')
for lab in ('H', 'R'):
    c = collections.Counter(x[lab] for x in L)
    print(f'sheet {lab}: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')))
H_ok = {c for c in cats if all(x['H'] == 'right' for x in L if x['function'] == c)}
s1, n1 = share('H', H_ok); s2, n2 = share('H', set(cats) - H_ok)
print(f'H fixes {s1:.2f} of {n1} N0 edge errors on functions whose decisions H states all right ({len(H_ok)}), '
      f'{s2:.2f} of {n2} elsewhere')
print('\nper function: N0 edge errors, share fixed by H / R / T, H labels')
for c in cats:
    s = [share(a, {c})[0] for a in ('H', 'R', 'T')]
    print(f'  {c:24s} {share("H", {c})[1]:3d}  ' + ' / '.join('  – ' if x != x else f'{x:.2f}' for x in s)
          + '   ' + ' '.join(x['H'][0] for x in L if x['function'] == c))

print('\npredictions')
print(f'W1 T fixes ≥ 0.85: {share("T")[0]:.2f} -> {"held" if share("T")[0] >= .85 else "failed"}')
print(f'W2 R ≥ T − 5: {hp["R"] - hp["T"]:+.1f} -> {"held" if hp["R"] >= hp["T"] - 5 else "failed"}')
print(f'W3 0.40 ≤ K ≤ 0.80: {k:.2f} -> {"held" if .4 <= k <= .8 else "failed"}')
print(f'W4 0.50 ≤ coverage ≤ 0.85 and transfer ≥ 0.80: {cov:.2f}, {tr:.2f} -> '
      f'{"held" if .5 <= cov <= .85 and tr >= .8 else "failed"}')
print(f'W5 N0 < 65%: {hp["N0"]:.1f} -> {"held" if hp["N0"] < 65 else "failed"}')
print(f'Kill K < 0.25: {"FIRED" if k < .25 else "did not fire"}')
print('Rules: ' + '; '.join(m for m, c in [
    ('K ≥ 0.85: the interview is not the leak with a consistent owner', k >= .85),
    ('coverage < 0.6 with transfer ≥ 0.8: the leak is what Hive asks', cov < .6 and tr >= .8),
    ('transfer < 0.7: the leak is writing answers as rules', tr < .7),
    ('R < T − 10: complete prose rules still lose to examples', hp['R'] < hp['T'] - 10)] if c) or 'none fired')
