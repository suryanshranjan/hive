"""G42 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python3 gates/gate42/referee/analyze.py <dir with probe_<arm>.json[.gz], wind_tunnel.json>
Sheets: D = what N0's code does, as rules (describer); C = D after the owner's review; H = interview; R = complete.
C1: D addresses (right, partial or wrong) ≥ 0.90 of the 25 declared decisions.
C2: C states ≥ 0.85 of decisions right, and H ≤ 0.60.
C3: hp_C − hp_H ≥ +10 (paired by function, bootstrap CI).      C4: hp_C ≥ 90.      C5: hp_R ≥ 95.
C6: of the decisions D states wrong or partly, C states ≥ 0.80 right (the review repairs what the code got wrong).
C7: hp_N0 < 65.      Kill: hp_C ≤ hp_H.      Ship: hp_C − hp_H ≥ +5."""
import collections, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'H', 'C', 'R')
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
rng = random.Random(42)
dd = [100 * (F['C'][c] - F['H'][c]) for c in cats]
bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
diff = sum(dd) / len(dd)
print(f'C − H = {diff:+.1f} points (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f}, bootstrap over functions)')

w = json.load(open(os.path.join(d, 'wind_tunnel.json'))); L = w['labels']; n = len(L)
for a in ('D', 'C', 'H', 'R'):
    c = collections.Counter(x[a] for x in L)
    print(f'sheet {a}: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')))
addressed = sum(x['D'] != 'absent' for x in L) / n
right = {a: sum(x[a] == 'right' for x in L) / n for a in ('D', 'C', 'H', 'R')}
bad = [x for x in L if x['D'] in ('wrong', 'partial')]
repaired = sum(x['C'] == 'right' for x in bad) / len(bad) if bad else float('nan')
spoiled = sum(x['D'] == 'right' and x['C'] != 'right' for x in L)
print(f'D: {len(w["D"])} rules; C: {len(w["C"])} rules; the owner marked {len(w["marked"])} rules, '
      f'{len(w["review"])} replies in review')
print(f'D addresses {addressed:.2f} of decisions; the review repaired {sum(x["C"] == "right" for x in bad)} of {len(bad)} '
      f'wrong or partial ({repaired:.2f}); spoiled {spoiled} right ones; absent in D made right in C: '
      f'{sum(x["D"] == "absent" and x["C"] == "right" for x in L)}')
print('\nper function: N0 edge errors, share fixed by H / C / R; labels D | C')
for f in cats:
    s = [share(a, {f})[0] for a in ('H', 'C', 'R')]
    print(f'  {f:24s} {share("H", {f})[1]:3d}  ' + ' / '.join('  – ' if x != x else f'{x:.2f}' for x in s) + '   '
          + ' '.join(x['D'][0] for x in L if x['function'] == f) + ' | ' + ' '.join(x['C'][0] for x in L if x['function'] == f))

print('\npredictions')
for tag, text, held in [
        ('C1', f'D addresses ≥ 0.90: {addressed:.2f}', addressed >= .9),
        ('C2', f'C right ≥ 0.85 and H ≤ 0.60: {right["C"]:.2f}, {right["H"]:.2f}', right['C'] >= .85 and right['H'] <= .6),
        ('C3', f'C − H ≥ +10: {diff:+.1f}', diff >= 10),
        ('C4', f'C ≥ 90%: {hp["C"]:.1f}', hp['C'] >= 90),
        ('C5', f'R ≥ 95%: {hp["R"]:.1f}', hp['R'] >= 95),
        ('C6', f'review repairs ≥ 0.80 of D\'s wrong or partial: {repaired:.2f}', repaired >= .8),
        ('C7', f'N0 < 65%: {hp["N0"]:.1f}', hp['N0'] < 65)]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Kill C ≤ H: {"FIRED" if hp["C"] <= hp["H"] else "did not fire"}')
print(f'Ship rule (C − H ≥ +5): {"FIRED" if diff >= 5 else "did not fire"}')
