"""G70 registered analysis (committed with the predictions, before the run):
    python3 gates/gate70/referee/analyze.py runs/g70a runs/g70b
Overnight, the owner away. HV = Hive's morning hand-over of a no-question build; QA = fresh builders given his morning
answers to the questions the night build recorded. Owner load: characters he read (questions, or the hand-over's screens).
M1 QA hidden >= HV + 10       M2 QA's owner reads <= 0.3x HV's       M3 QA hidden >= QN (the night build itself) + 15
Ship (overnight builds record questions; the owner answers them in the morning, then a fix build): M1 and M2."""
import collections, csv, gzip, json, os, random, sys
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))
def per_fn(P):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in t}
ARMS = ('N0', 'QN', 'HV', 'QA')
hp = collections.defaultdict(list); F_all = collections.defaultdict(list); ch = collections.defaultdict(list); nq = []
for d in sys.argv[1:]:
    F = {a: per_fn(load(os.path.join(d, f'probe_{a}.json'))) for a in ARMS}; cats = sorted(F['N0'])
    for a in ARMS:
        hp[a].append(100 * sum(F[a].values()) / len(cats)); F_all[a] += [F[a][c] for c in cats]
    w = json.load(open(os.path.join(d, 'sheet.json')))
    ch['QA'].append(sum(len(x['question']) + len(x['answer']) for x in w['QA'])); nq.append(len(w['QA']))
    ch['HV'].append(len(w['list_review']['transcript']) + len(w['spot_review']['transcript']))
    L = w['labels']
    print(f"== {d}: hidden " + ', '.join(f'{a} {hp[a][-1]:.1f}%' for a in ARMS) + f"; {nq[-1]} questions recorded; owner reads QA "
          f"{ch['QA'][-1]} chars, HV {ch['HV'][-1]} chars; sheet right " + ', '.join(f"{a} {sum(x[a] == 'right' for x in L)}" for a in ('D', 'SL', 'HV', 'QA', 'R')))
m = lambda v: sum(v) / len(v); mh = {a: m(hp[a]) for a in ARMS}; rng = random.Random(70)
def ci(a, b):
    dd = [100 * (x - y) for x, y in zip(F_all[a], F_all[b])]
    bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(4000))
    return f'{m(dd):+.1f} (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f})'
print('\npooled hidden: ' + ', '.join(f'{a} {mh[a]:.1f}%' for a in ARMS))
for a, b in (('QA', 'HV'), ('QA', 'QN'), ('HV', 'N0')):
    print(f'{a} − {b}: {ci(a, b)}')
print(f"questions recorded per run {m(nq):.1f}; owner reads QA {m(ch['QA']):.0f}, HV {m(ch['HV']):.0f} chars")
res = [('M1', f"QA ≥ HV + 10: {mh['QA'] - mh['HV']:+.1f}", mh['QA'] - mh['HV'] >= 10),
       ('M2', f"QA's owner reads ≤ 0.3 × HV's: {m(ch['QA']) / m(ch['HV']):.2f}", m(ch['QA']) <= .3 * m(ch['HV'])),
       ('M3', f"QA ≥ QN + 15: {mh['QA'] - mh['QN']:+.1f}", mh['QA'] - mh['QN'] >= 15)]
print('\npredictions')
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
print(f"Ship (morning questions overnight): {'FIRED' if res[0][2] and res[1][2] else 'did not fire'}")
