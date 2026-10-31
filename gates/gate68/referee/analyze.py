"""G68 registered analysis (committed with the predictions, before the run). From the repo root:
    python3 gates/gate68/referee/analyze.py runs/g68a runs/g68b
Q1 SQ hidden >= CQ - 3 (a swarm that asks matches one agent that asks)      Q2 SQH hidden >= SQ + 3 (the hand-over adds)
Q3 SQ's questions <= 1.5x CQ's (the team shares answers instead of re-asking)
If Q2 fails with SQH - SQ < +3: after a build in which builders asked the owner, Hive skips the long hand-over (it stays
for builds he could not answer, e.g. overnight). If Q2 holds: keep both."""
import collections, csv, gzip, json, os, random, sys
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
def per_fn(P):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in t}
ARMS = ('CQ', 'SQ', 'SQH')
hp = collections.defaultdict(list); F_all = collections.defaultdict(list); q = collections.defaultdict(list); cost = collections.defaultdict(list)
for d in sys.argv[1:]:
    F = {a: per_fn(load(os.path.join(d, f'probe_{a}.json'))) for a in ARMS}
    cats = sorted(F['CQ'])
    for a in ARMS:
        hp[a].append(100 * sum(F[a].values()) / len(cats)); F_all[a] += [F[a][c] for c in cats]
    for a in ('CQ', 'SQ'):
        p = os.path.join(d, f'owner_{a}.jsonl'); q[a].append(sum(1 for _ in open(p)) if os.path.exists(p) else 0)
    w = json.load(open(os.path.join(d, 'sheet.json')))
    q['SQH_replies'].append(w['list_review']['replies'] + w['spot_review']['replies'])
    rows = collections.defaultdict(float)
    for r in csv.DictReader(open(os.path.join(d, 'agents.csv'))): rows[r['worker'].split('-w')[0]] += float(r['cost_usd'] or 0)
    for a in ARMS: cost[a].append(rows[a] + (rows['SQ'] + sum(float(w['cost_usd'].get(k) or 0) for k in ('describer', 'spotter')) if a == 'SQH' else 0))
    L = w['labels']
    print(f"== {d}: hidden " + ', '.join(f'{a} {hp[a][-1]:.1f}%' for a in ARMS) + f"; questions CQ {q['CQ'][-1]}, SQ {q['SQ'][-1]}; "
          f"SQH owner replies {q['SQH_replies'][-1]}; cost " + ', '.join(f'{a} ${cost[a][-1]:.2f}' for a in ARMS)
          + '; sheet right ' + ', '.join(f"{a} {sum(x[a] == 'right' for x in L)}" for a in ('D', 'SL', 'HV', 'R')))
m = lambda v: sum(v) / len(v); mh = {a: m(hp[a]) for a in ARMS}; rng = random.Random(68)
def ci(a, b):
    dd = [100 * (x - y) for x, y in zip(F_all[a], F_all[b])]
    bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
    return f'{m(dd):+.1f} (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f})'
print('\npooled hidden: ' + ', '.join(f'{a} {mh[a]:.1f}%' for a in ARMS))
for a, b in (('SQ', 'CQ'), ('SQH', 'SQ'), ('SQH', 'CQ')):
    print(f'{a} − {b}: {ci(a, b)}')
print(f"questions per run: CQ {m(q['CQ']):.1f}, SQ {m(q['SQ']):.1f}; SQH's extra owner replies {m(q['SQH_replies']):.1f}; cost per run "
      + ', '.join(f'{a} ${m(cost[a]):.2f}' for a in ARMS))
res = [('Q1', f"SQ ≥ CQ − 3: {mh['SQ'] - mh['CQ']:+.1f}", mh['SQ'] - mh['CQ'] >= -3),
       ('Q2', f"SQH ≥ SQ + 3: {mh['SQH'] - mh['SQ']:+.1f}", mh['SQH'] - mh['SQ'] >= 3),
       ('Q3', f"SQ questions ≤ 1.5 × CQ's: {m(q['SQ']):.1f} vs {m(q['CQ']):.1f}", m(q['SQ']) <= 1.5 * m(q['CQ']))]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Skip the long hand-over after builds whose builders asked: {'FIRED' if not res[1][2] else 'did not fire'}")
