"""G44 registered analysis (committed with the predictions, before the rules exist). Run from the repo root:
    python3 gates/gate44/referee/analyze.py <dir with probe_<arm>.json[.gz], agents.csv, sheet.json, board_*.txt>
2 × 2: rules (none / the corrected code sheet, Gate 42) × builders (silent / talking on a shared board).
P1: hp_C ≥ 95.     P2: |hp_CT − hp_C| ≤ 3.     P3: |hp_NT − hp_N0| ≤ 8.
P4: each talking team posts ≥ 3 messages.     P5: cost_CT ≤ 1.10 × cost_C.
Ship talking: hp_CT − hp_C ≥ +3 and hp_NT − hp_N0 ≥ +5.     Kill for talking: hp_CT ≤ hp_C and hp_NT ≤ hp_N0."""
import collections, csv, gzip, json, os, random, sys

d = sys.argv[1]
arms = ('N0', 'NT', 'C', 'CT')
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
cost = collections.defaultdict(float)
for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): cost[r['worker'].split('-w')[0]] += float(r['cost_usd'] or 0)
msgs = {a: (open(os.path.join(d, f'board_{a}.txt')).read().splitlines() if os.path.exists(os.path.join(d, f'board_{a}.txt')) else [])
        for a in ('NT', 'CT')}
print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in arms))
print('builder cost: ' + ', '.join(f'{a} ${cost[a]:.2f}' for a in arms))
print('messages: ' + ', '.join(f'{a} {len(m)}' for a, m in msgs.items()))
e = [k for k, v in ok['N0'].items() if not v]; g = [k for k, v in ok['N0'].items() if v]
for a in arms[1:]:
    print(f'{a}: fixes {sum(ok[a][k] for k in e) / len(e):.2f} of {len(e)} N0 edge errors; breaks {sum(not ok[a][k] for k in g)} of {len(g)}')
rng = random.Random(44)
def paired(a, b):
    dd = [100 * (F[a][c] - F[b][c]) for c in cats]
    bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
    return sum(dd) / len(dd), bs[100], bs[3899]
for a, b in (('NT', 'N0'), ('CT', 'C'), ('C', 'N0'), ('CT', 'NT')):
    m, lo, hi = paired(a, b); print(f'{a} − {b} = {m:+.1f} points (95% CI {lo:+.1f} to {hi:+.1f})')
s = json.load(open(os.path.join(d, 'sheet.json')))
print(f'code sheet: {len(s["D"])} rules, owner marked {len(s["marked"])}, {len(s["C"])} after review')
print('\npredictions')
for tag, text, held in [
        ('P1', f'C ≥ 95%: {hp["C"]:.1f}', hp['C'] >= 95),
        ('P2', f'|CT − C| ≤ 3: {hp["CT"] - hp["C"]:+.1f}', abs(hp['CT'] - hp['C']) <= 3),
        ('P3', f'|NT − N0| ≤ 8: {hp["NT"] - hp["N0"]:+.1f}', abs(hp['NT'] - hp['N0']) <= 8),
        ('P4', f'each talking team ≥ 3 messages: {len(msgs["NT"])}, {len(msgs["CT"])}', min(len(m) for m in msgs.values()) >= 3),
        ('P5', f'cost CT ≤ 1.10 × C: {cost["CT"] / cost["C"]:.2f}×', cost['CT'] <= 1.1 * cost['C'])]:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f'Ship talking (CT − C ≥ +3 and NT − N0 ≥ +5): {"FIRED" if hp["CT"] - hp["C"] >= 3 and hp["NT"] - hp["N0"] >= 5 else "did not fire"}')
print(f'Kill for talking (no gain with or without rules): {"FIRED" if hp["CT"] <= hp["C"] and hp["NT"] <= hp["N0"] else "did not fire"}')
