"""G60 registered analysis (committed with the predictions, before the run). Run from the repo root:
    python3 gates/gate60/referee/analyze.py <run dir>:<oracle.py> [<run dir>:<oracle.py> ...]
Each run dir holds probe_<arm>.json[.gz] and sheet.json (runs/g60a, runs/g60b, or their copies in gates/gate60/results).
Pooled over the runs (each run's 25ish declared decisions counted once):
W1  of the prober's calls where N0's result differs from the policy, the two builds (N0, B) disagree on >= 50%
W2  DG states at least as many declared decisions right as CB
W3  DG shows at most 70% as many cases as CB
W4  hidden DG >= hidden CB - 3 points (mean over runs)
W5  DG states >= 2 more decisions right than SL
Ship (spot checks are drawn from where two builds disagree): W2, W3 and W4 hold.
Replace outright: DG right >= CB right + 3 and hidden DG >= CB + 5.
Kill: DG right <= CB right - 2 and hidden DG <= CB - 5."""
import collections, gzip, json, os, random, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import wings

ARMS = ('N0', 'B', 'SL', 'CB', 'DG')
def load(p):
    return json.load(gzip.open(p + '.gz')) if os.path.exists(p + '.gz') else json.load(open(p))

def per_fn(P):
    t = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in P: t[r['cat']][r['test']].append(r['ok'])
    return {c: sum(all(v) for v in t[c].values()) / len(t[c]) for c in t}

tot = collections.Counter(); hp_all = collections.defaultdict(list); diffs = []; rec = collections.Counter()
for arg in sys.argv[1:]:
    d, oracle = arg.rsplit(':', 1)
    print(f'== {d}')
    F = {a: per_fn(load(os.path.join(d, f'probe_{a}.json'))) for a in ARMS if os.path.exists(os.path.join(d, f'probe_{a}.json'))
         or os.path.exists(os.path.join(d, f'probe_{a}.json.gz'))}
    cats = sorted(F['N0'])
    hp = {a: 100 * sum(F[a].values()) / len(cats) for a in F}
    for a in hp: hp_all[a].append(hp[a])
    print('hidden pass: ' + ', '.join(f'{a} {hp[a]:.1f}%' for a in hp))
    diffs += [100 * (F['DG'][c] - F['CB'][c]) for c in cats]
    w = json.load(open(os.path.join(d, 'sheet.json'))); L = w['labels']
    for a in ('D', 'SL', 'CB', 'DG', 'R'):
        c = collections.Counter(x[a] for x in L); tot[(a, 'right')] += c['right']; tot[(a, 'partial')] += c['partial']
        print(f'{a}: ' + ', '.join(f'{v} {c[v]}' for v in ('right', 'partial', 'wrong', 'absent')))
    tot['decisions'] += len(L)
    for a in ('CB', 'DG'):
        r = w['reviews'][a]; fx = r['fixes']; conf = sum(1 for f in fx if f.get('confirmed'))
        tot[(a, 'shown')] += len(r['shown']); tot[(a, 'fixes')] += len(fx); tot[(a, 'confirmed')] += conf
        tot[(a, 'spoiled')] += sum(x['SL'] == 'right' and x[a] != 'right' for x in L)
        print(f"{a}: {len(r['shown'])} cases shown, {len(fx)} corrected, {conf} confirmed on re-show, "
              f"{r['minutes']} min, owner model cost ${r['spots']['cost']}")
    # W1: the referee runs the policy on the prober's calls; never shown to anyone before scoring
    wg = w['wings']; agg = next((c['function'] for c in wg['calls'] if 'values' in c), '')
    with tempfile.TemporaryDirectory() as t:
        json.dump(wg['calls'], open(os.path.join(t, 'c.json'), 'w'))
        subprocess.run([sys.executable, os.path.join(HERE, 'wings.py'), 'run', os.path.abspath(oracle), os.path.join(t, 'c.json'),
                        agg, os.path.join(t, 'o.json')], check=True, cwd='/')
        O = json.load(open(os.path.join(t, 'o.json')))
    wrong = [i for i, (a, o) in enumerate(zip(wg['A'], O)) if a and o and not wings.same(a, o)]
    dis = [i for i, (a, b) in enumerate(zip(wg['A'], wg['B'])) if a and b and not wings.same(a, b)]
    caught = len(set(wrong) & set(dis))
    rec['wrong'] += len(wrong); rec['caught'] += caught; rec['dis'] += len(dis)
    rec['dis_wrong'] += sum(1 for i in dis if i in set(wrong))
    print(f"wings: {len(wg['calls'])} calls; N0 differs from the policy on {len(wrong)}; the builds disagree on {len(dis)}; "
          f"both: {caught} (recall {caught / max(1, len(wrong)):.2f}); of disagreements, N0 wrong on "
          f"{sum(1 for i in dis if i in set(wrong)) / max(1, len(dis)):.2f}")
    per = {f: (v['disagree'], v['calls']) for f, v in wg['per_function'].items()}
    print('disagreements per function: ' + ', '.join(f'{f} {a}/{n}' for f, (a, n) in per.items()))

print('\n== pooled')
n = tot['decisions']
for a in ('D', 'SL', 'CB', 'DG', 'R'):
    print(f"{a}: right {tot[(a, 'right')]} of {n}, partial {tot[(a, 'partial')]}")
mean = {a: sum(v) / len(v) for a, v in hp_all.items()}
print('hidden pass (mean over runs): ' + ', '.join(f'{a} {v:.1f}%' for a, v in mean.items()))
rng = random.Random(60)
bs = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(4000))
print(f'DG − CB = {sum(diffs) / len(diffs):+.1f} points per function (95% CI {bs[100]:+.1f} to {bs[3899]:+.1f}, bootstrap over functions)')
for a in ('CB', 'DG'):
    print(f"{a}: {tot[(a, 'shown')]} cases shown, {tot[(a, 'fixes')]} corrected, {tot[(a, 'confirmed')]} confirmed, "
          f"{tot[(a, 'spoiled')]} decisions SL had right spoiled")
recall = rec['caught'] / max(1, rec['wrong'])
rD, rC, rS = tot[('DG', 'right')], tot[('CB', 'right')], tot[('SL', 'right')]
share = tot[('DG', 'shown')] / max(1, tot[('CB', 'shown')])
print('\npredictions')
res = [('W1', f'disagreement recall of N0 errors ≥ 0.50: {recall:.2f} ({rec["caught"]} of {rec["wrong"]})', recall >= .5),
       ('W2', f'DG right ≥ CB right: {rD} vs {rC}', rD >= rC),
       ('W3', f'DG cases ≤ 70% of CB cases: {share:.2f}', share <= .7),
       ('W4', f'hidden DG ≥ CB − 3: {mean["DG"] - mean["CB"]:+.1f}', mean['DG'] - mean['CB'] >= -3),
       ('W5', f'DG right ≥ SL right + 2: {rD} vs {rS}', rD >= rS + 2)]
for tag, text, held in res:
    print(f'{tag} {text} -> {"held" if held else "failed"}')
ok = {t: h for t, _, h in res}
print(f"Ship (cases from disagreements): {'FIRED' if ok['W2'] and ok['W3'] and ok['W4'] else 'did not fire'}")
print(f"Replace outright: {'FIRED' if rD >= rC + 3 and mean['DG'] - mean['CB'] >= 5 else 'did not fire'}")
print(f"Kill: {'FIRED' if rD <= rC - 2 and mean['DG'] - mean['CB'] <= -5 else 'did not fire'}")
