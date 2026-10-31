"""G66 registered analysis (committed with the predictions, before the run). From the repo root:
    python3 gates/gate66/referee/analyze.py runs/g66a runs/g66b
Hidden pass per arm (mean over runs; paired by function); owner load: CC and CQ = questions asked and characters he read
(the questions); HV = his replies and characters he read (the list review's and the spot checks' screens).
B1 HV >= CC + 10      B2 HV >= CQ + 5      B3 CQ asks >= 15 questions per run (mean)      B4 CC asks <= 5 per run (mean)
B5 HV's owner reads >= 2x the characters CQ's does
Headline (Hive beats a Claude Code agent with the same owner, wind tunnel): B1 and B2.
If CQ >= HV: asking first matches Hive's hand-over; next, test them combined."""
import collections, csv, gzip, json, os, random, sys
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
def per_fn(P):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in t}
ARMS = ('N0', 'CC', 'CQ', 'HV')
hp = collections.defaultdict(list); F_all = collections.defaultdict(list); q = collections.defaultdict(list); chars = collections.defaultdict(list)
cost = collections.defaultdict(list); turns = collections.defaultdict(list)
for d in sys.argv[1:]:
    F = {a: per_fn(load(os.path.join(d, f'probe_{a}.json'))) for a in ARMS}
    cats = sorted(F['N0'])
    for a in ARMS:
        hp[a].append(100 * sum(F[a].values()) / len(cats)); F_all[a] += [F[a][c] for c in cats]
    for a in ('CC', 'CQ'):
        p = os.path.join(d, f'owner_{a}.jsonl'); L = [json.loads(x) for x in open(p)] if os.path.exists(p) else []
        q[a].append(len(L)); chars[a].append(sum(len(x['question']) for x in L)); turns[a].append(len(L))
    w = json.load(open(os.path.join(d, 'sheet.json')))
    chars['HV'].append(len(w['list_review']['transcript']) + len(w['spot_review']['transcript']))
    turns['HV'].append(w['list_review']['replies'] + w['spot_review']['replies'])
    rows = collections.defaultdict(float)
    for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): rows[r['worker'].split('-w')[0]] += float(r['cost_usd'] or 0)
    hive_side = sum(float(w['cost_usd'].get(k) or 0) for k in ('describer', 'spotter'))
    for a in ARMS: cost[a].append(rows[a] + (rows['N0'] + hive_side if a == 'HV' else 0))
    L = w['labels']
    print(f"== {d}: hidden " + ', '.join(f'{a} {hp[a][-1]:.1f}%' for a in ARMS) + f"; questions CC {q['CC'][-1]}, CQ {q['CQ'][-1]}; "
          f"HV owner replies {turns['HV'][-1]}; chars read CC {chars['CC'][-1]}, CQ {chars['CQ'][-1]}, HV {chars['HV'][-1]}; "
          f"cost " + ', '.join(f'{a} ${cost[a][-1]:.2f}' for a in ARMS) + '; sheet right ' + ', '.join(f"{a} {sum(x[a] == 'right' for x in L)}" for a in ('D', 'SL', 'HV', 'R')))
m = lambda v: sum(v) / len(v)
mh = {a: m(hp[a]) for a in ARMS}
rng = random.Random(66)
def ci(a, b):
    dd = [100 * (x - y) for x, y in zip(F_all[a], F_all[b])]
    bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
    return f'{m(dd):+.1f} (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f})'
print('\npooled hidden: ' + ', '.join(f'{a} {mh[a]:.1f}%' for a in ARMS))
for a, b in (('HV', 'CC'), ('HV', 'CQ'), ('CQ', 'CC'), ('CC', 'N0')):
    print(f'{a} − {b}: {ci(a, b)}')
print(f"owner: questions CC {m(q['CC']):.1f}, CQ {m(q['CQ']):.1f} per run; HV replies {m(turns['HV']):.1f}; chars read CC {m(chars['CC']):.0f}, "
      f"CQ {m(chars['CQ']):.0f}, HV {m(chars['HV']):.0f}; cost per run " + ', '.join(f'{a} ${m(cost[a]):.2f}' for a in ARMS))
res = [('B1', f"HV ≥ CC + 10: {mh['HV'] - mh['CC']:+.1f}", mh['HV'] - mh['CC'] >= 10),
       ('B2', f"HV ≥ CQ + 5: {mh['HV'] - mh['CQ']:+.1f}", mh['HV'] - mh['CQ'] >= 5),
       ('B3', f"CQ asks ≥ 15 per run: {m(q['CQ']):.1f}", m(q['CQ']) >= 15),
       ('B4', f"CC asks ≤ 5 per run: {m(q['CC']):.1f}", m(q['CC']) <= 5),
       ('B5', f"HV owner reads ≥ 2× CQ's: {m(chars['HV']) / max(1, m(chars['CQ'])):.1f}×", m(chars['HV']) >= 2 * m(chars['CQ']))]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Headline (Hive beats Claude Code with the same owner): {'FIRED' if res[0][2] and res[1][2] else 'did not fire'}")
print(f"Asking first matches the hand-over (CQ ≥ HV): {'YES' if mh['CQ'] >= mh['HV'] else 'no'}")
